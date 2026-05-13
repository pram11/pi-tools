use std::collections::HashMap;

use crate::backend::comrak::ComrakBackend;
use crate::backend::custom::CustomBackend;
use crate::converter::{Converter, ConverterError, Result};
use crate::post_processor;

pub fn get_backend(name: &str) -> Result<&'static dyn Converter> {
    static BACKENDS: std::sync::OnceLock<HashMap<&'static str, &'static dyn Converter>> =
        std::sync::OnceLock::new();
    BACKENDS
        .get_or_init(|| {
            let mut m: HashMap<&'static str, &'static dyn Converter> = HashMap::new();
            m.insert("comrak", &ComrakBackend);
            m.insert("custom", &CustomBackend);
            m
        })
        .get(name)
        .copied()
        .ok_or_else(|| ConverterError::UnknownBackend(name.to_string()))
}

pub fn convert(html: &str, backend: &str) -> Result<String> {
    let converter = get_backend(backend)?;
    let raw = converter.convert(html)?;
    Ok(post_processor::process(&raw))
}
