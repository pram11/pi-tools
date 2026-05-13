use llama_cpp_2::context::params::{LlamaContextParams, LlamaPoolingType};
use llama_cpp_2::llama_backend::LlamaBackend;
use llama_cpp_2::llama_batch::LlamaBatch;
use llama_cpp_2::model::params::LlamaModelParams;
use llama_cpp_2::model::LlamaModel;
use std::num::NonZeroU32;
use std::path::Path;
use std::sync::Mutex;

pub const EMBEDDING_DIM: usize = 768;
/// Max context size matching model n_ctx_train (nomic-embed-text-v1.5)
const MAX_CTX: u32 = 2048;
/// Max tokens per embedding request (reserve 2 for BOS + margin)
const MAX_TOKENS: usize = (MAX_CTX - 2) as usize;

struct EmbedderState {
    backend: LlamaBackend,
    model: LlamaModel,
}

static EMBEDDER: Mutex<Option<EmbedderState>> = Mutex::new(None);

fn ensure_embedder(model_path: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let mut state = EMBEDDER.lock().unwrap();
    if state.is_none() {
        let backend = LlamaBackend::init()?;
        let model = LlamaModel::load_from_file(&backend, model_path, &LlamaModelParams::default())?;
        *state = Some(EmbedderState { backend, model });
    }
    Ok(())
}

fn normalize(v: &mut Vec<f32>) {
    let norm: f32 = v.iter().map(|x| x * x).sum::<f32>().sqrt();
    if norm > 0.0 {
        for val in v.iter_mut() {
            *val /= norm;
        }
    }
}

pub fn embed_text(model_path: &Path, text: &str) -> Result<Vec<f32>, Box<dyn std::error::Error>> {
    ensure_embedder(model_path)?;
    let mut state = EMBEDDER.lock().unwrap();
    let state = state.as_mut().unwrap();

    let ctx_params = LlamaContextParams::default()
        .with_embeddings(true)
        .with_pooling_type(LlamaPoolingType::Mean)
        .with_n_ctx(NonZeroU32::new(MAX_CTX))
        .with_n_ubatch(MAX_CTX)
        .with_n_batch(MAX_CTX);

    let mut ctx = state.model.new_context(&state.backend, ctx_params)?;

    // Tokenize
    use llama_cpp_2::model::AddBos;
    let tokens = state.model.str_to_token(text, AddBos::Always)?;

    if tokens.is_empty() {
        return Ok(vec![0.0; EMBEDDING_DIM]);
    }

    // Safety: truncate tokens exceeding model context capacity
    let tokens: Vec<_> = if tokens.len() > MAX_TOKENS {
        tokens[..MAX_TOKENS].to_vec()
    } else {
        tokens
    };

    // Create batch
    let mut batch = LlamaBatch::new(tokens.len(), 1);
    for (i, token) in tokens.iter().enumerate() {
        batch.add(*token, i as i32, &[0], true)?;
    }

    // Encode
    ctx.encode(&mut batch)?;

    // Get embeddings
    let emb_raw = ctx.embeddings_seq_ith(0)?;
    let mut emb = emb_raw.to_vec();

    // Trim/pad to EMBEDDING_DIM
    if emb.len() > EMBEDDING_DIM {
        emb.truncate(EMBEDDING_DIM);
    } else if emb.len() < EMBEDDING_DIM {
        emb.resize(EMBEDDING_DIM, 0.0);
    }

    normalize(&mut emb);
    Ok(emb)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn model_path() -> &'static Path {
        Path::new("/root/.pi/agent/skills/knowledge-base/models/nomic-embed-text-v1.5.Q4_K_M.gguf")
    }

    #[test]
    fn test_embed_produces_768_dim() {
        let emb = embed_text(model_path(), "hello world").expect("embed");
        assert_eq!(emb.len(), EMBEDDING_DIM, "must be 768 dims");
    }

    #[test]
    fn test_embed_normalized() {
        let emb = embed_text(model_path(), "test normalization").expect("embed");
        let norm: f32 = emb.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!((norm - 1.0).abs() < 1e-4, "must be unit vector, got {}", norm);
    }

    #[test]
    fn test_same_text_same_embedding() {
        let e1 = embed_text(model_path(), "identical text").expect("embed");
        let e2 = embed_text(model_path(), "identical text").expect("embed");
        let diff: f32 = e1.iter().zip(&e2).map(|(a, b)| (a - b).abs()).sum();
        assert!(diff < 1e-5, "same text → same embedding, diff={}", diff);
    }

    #[test]
    fn test_different_text_different_embedding() {
        let e1 = embed_text(model_path(), "apple").expect("embed");
        let e2 = embed_text(model_path(), "quantum physics").expect("embed");
        let dot: f32 = e1.iter().zip(&e2).map(|(a, b)| a * b).sum();
        assert!(dot < 0.99, "different texts should have low similarity, got {}", dot);
    }

    /// Regression: default n_ubatch=512 crashes when token count > 512.
    /// This test generates text that produces ~1000 tokens.
    #[test]
    fn test_embed_large_text_over_512_tokens() {
        // ~1000 words → ~1000+ tokens, well above default n_ubatch=512
        let big_text = "lorem ipsum dolor sit amet ".repeat(256);
        let emb = embed_text(model_path(), &big_text).expect("embed large text");
        assert_eq!(emb.len(), EMBEDDING_DIM);
        let norm: f32 = emb.iter().map(|x| x * x).sum::<f32>().sqrt();
        assert!((norm - 1.0).abs() < 1e-3, "normalized, got {}", norm);
    }
}
