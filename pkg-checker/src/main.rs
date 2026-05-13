use serde::Deserialize;
use serde_json::Value;
use std::env;
use std::process;

type Err = Box<dyn std::error::Error + Send + Sync>;
type Res<T> = Result<T, Err>;

static USER_AGENT: &str = "pkg-checker/1.0 (https://github.com/pkg-checker)";

fn client() -> reqwest::Client {
    reqwest::Client::builder()
        .user_agent(USER_AGENT)
        .build()
        .unwrap()
}

async fn fetch_json<T: serde::de::DeserializeOwned>(url: &str) -> Result<T, reqwest::Error> {
    client().get(url).send().await?.error_for_status()?.json().await
}

// ─── Crates.io ───────────────────────────────────────────────────────────────

#[derive(Deserialize)]
struct CrateMeta {
    #[serde(rename = "crate")]
    crate_info: CrateInfo,
}
#[derive(Deserialize)]
struct CrateInfo {
    name: String,
    max_version: String,
    homepage: Option<String>,
    documentation: Option<String>,
}
#[derive(Deserialize)]
struct CrateDeps {
    dependencies: Vec<CrateDep>,
}
#[derive(Deserialize)]
struct CrateDep {
    name: String,
    req: String,
    kind: Option<String>,
}

async fn check_crate(pkg: &str) -> Res<()> {
    let meta: CrateMeta = fetch_json(&format!("https://crates.io/api/v1/crates/{pkg}")).await?;

    println!("Package: {}", meta.crate_info.name);
    println!("Ecosystem: crate");
    println!("Latest: {}", meta.crate_info.max_version);
    if let Some(docs) = &meta.crate_info.documentation {
        println!("Docs: {}", docs);
    } else if let Some(home) = &meta.crate_info.homepage {
        println!("Homepage: {}", home);
    }

    let deps_url = format!(
        "https://crates.io/api/v1/crates/{}/{}/dependencies",
        pkg, meta.crate_info.max_version
    );
    let mut deps = CrateDeps { dependencies: Vec::new() };
    if let Ok(resp) = client().get(&deps_url).send().await {
        if resp.status().is_success() {
            if let Ok(parsed) = resp.json::<CrateDeps>().await {
                deps = parsed;
            }
        }
    }

    let normal: Vec<_> = deps.dependencies.iter()
        .filter(|d| d.kind.as_deref() == Some("normal") || d.kind.is_none())
        .collect();
    let dev: Vec<_> = deps.dependencies.iter()
        .filter(|d| matches!(d.kind.as_deref(), Some("dev") | Some("build")))
        .collect();

    if !normal.is_empty() {
        println!("Dependencies:");
        for d in &normal {
            println!("  - {} ({})", d.name, d.req);
        }
    }
    if !dev.is_empty() {
        println!("Dev Dependencies:");
        for d in &dev {
            println!("  - {} ({})", d.name, d.req);
        }
    }
    Ok(())
}

// ─── PyPI ────────────────────────────────────────────────────────────────────

async fn check_pip(pkg: &str) -> Res<()> {
    let data: Value = fetch_json(&format!("https://pypi.org/pypi/{}/json", pkg)).await?;

    let info = data["info"].as_object().ok_or("Invalid PyPI response")?;
    let name = info.get("name").and_then(|v| v.as_str()).unwrap_or(pkg);
    let version = info.get("version").and_then(|v| v.as_str()).unwrap_or("unknown");

    println!("Package: {}", name);
    println!("Ecosystem: pip");
    println!("Latest: {}", version);

    if let Some(urls) = info.get("project_urls").and_then(|v| v.as_object()) {
        if let Some(docs) = urls.get("Documentation").and_then(|v| v.as_str()) {
            println!("Docs: {}", docs);
        }
    }
    if let Some(home) = info.get("home_page").and_then(|v| v.as_str()).filter(|s| !s.is_empty()) {
        println!("Homepage: {}", home);
    }

    if let Some(reqs) = info.get("requires_dist").and_then(|v| v.as_array()) {
        let normal: Vec<_> = reqs.iter()
            .filter(|v| v.as_str().map_or(false, |s| !s.contains("extra ==")))
            .collect();
        let extras: Vec<_> = reqs.iter()
            .filter(|v| v.as_str().map_or(false, |s| s.contains("extra ==")))
            .collect();

        if !normal.is_empty() {
            println!("Dependencies:");
            for r in &normal {
                println!("  - {}", r.as_str().unwrap_or(""));
            }
        }
        if !extras.is_empty() {
            println!("Optional Dependencies:");
            for r in &extras {
                println!("  - {}", r.as_str().unwrap_or(""));
            }
        }
    }
    Ok(())
}

// ─── npm ─────────────────────────────────────────────────────────────────────

async fn check_npm(pkg: &str) -> Res<()> {
    let data: Value = fetch_json(&format!("https://registry.npmjs.org/{}", pkg)).await?;

    let name = data.get("name").and_then(|v| v.as_str()).unwrap_or(pkg);
    let tag_latest = data.get("dist-tags")
        .and_then(|v| v.get("latest"))
        .and_then(|v| v.as_str())
        .unwrap_or("unknown");

    println!("Package: {}", name);
    println!("Ecosystem: npm");
    println!("Latest: {}", tag_latest);

    let ver = data.get("versions").and_then(|v| v.get(tag_latest));
    if let Some(ver) = ver {
        if let Some(home) = ver.get("homepage").and_then(|v| v.as_str()) {
            println!("Homepage: {}", home);
        }
        if let Some(repo) = ver.get("repository") {
            let repo_url = repo.get("url").and_then(|v| v.as_str())
                .or_else(|| repo.as_str());
            if let Some(raw) = repo_url {
                let clean = raw.trim_start_matches("git+https://")
                    .trim_start_matches("git+ssh://git@")
                    .trim_start_matches("https://")
                    .trim_end_matches(".git");
                if raw.contains("github") {
                    let owner_repo = clean.trim_start_matches("github.com/");
                    println!("GitHub: https://github.com/{}", owner_repo);
                } else {
                    println!("Repo: {}", clean);
                }
            }
        }

        if let Some(deps) = ver.get("dependencies").and_then(|v| v.as_object()) {
            if !deps.is_empty() {
                println!("Dependencies:");
                for (k, v) in deps {
                    println!("  - {} ({})", k, v.as_str().unwrap_or("*"));
                }
            }
        }
        if let Some(dd) = ver.get("devDependencies").and_then(|v| v.as_object()) {
            if !dd.is_empty() {
                println!("Dev Dependencies:");
                for (k, v) in dd {
                    println!("  - {} ({})", k, v.as_str().unwrap_or("*"));
                }
            }
        }
    }
    Ok(())
}

// ─── Maven Central ───────────────────────────────────────────────────────────

async fn check_maven(pkg: &str, group: Option<&str>) -> Res<()> {
    let query = if let Some(g) = group {
        format!("https://search.maven.org/solrsearch/select?q=g:{}+AND+a:{}&rows=1&wt=json", g, pkg)
    } else {
        format!("https://search.maven.org/solrsearch/select?q=a:{}&rows=1&wt=json", pkg)
    };

    let data: Value = fetch_json(&query).await?;

    let doc = data["response"]["docs"].as_array()
        .and_then(|arr| arr.first())
        .ok_or("No results found")?;

    let group_id = doc.get("g").and_then(|v| v.as_str()).unwrap_or(pkg);
    let artifact_id = doc.get("a").and_then(|v| v.as_str()).unwrap_or(pkg);
    let version = doc.get("latestVersion").and_then(|v| v.as_str()).unwrap_or("unknown");

    println!("Package: {}:{}", group_id, artifact_id);
    println!("Ecosystem: maven");
    println!("Latest: {}", version);
    println!("Docs: https://www.javadoc.io/doc/{}/{}/{}", group_id, artifact_id, version);

    let pom_url = format!(
        "https://repo1.maven.org/maven2/{}/{}/{}/pom.xml",
        group_id.replace('.', "/"), artifact_id, version
    );

    if let Ok(resp) = client().get(&pom_url).send().await {
        if let Ok(text) = resp.text().await {
        let mut in_deps = false;
        let mut in_dep = false;
        let mut g = String::new();
        let mut a = String::new();
        let mut scope = String::new();
        let mut normal: Vec<String> = Vec::new();
        let mut test: Vec<String> = Vec::new();

        for line in text.lines() {
            let t = line.trim();
            if t == "<dependencies>" { in_deps = true; continue; }
            if t == "</dependencies>" { in_deps = false; continue; }
            if !in_deps { continue; }
            if t == "<dependency>" {
                in_dep = true; g.clear(); a.clear(); scope.clear();
                continue;
            }
            if t == "</dependency>" {
                in_dep = false;
                let entry = format!("{}:{}", g, a);
                if scope == "test" || scope == "provided" {
                    test.push(entry);
                } else {
                    normal.push(entry);
                }
                continue;
            }
            if in_dep {
                if t.starts_with("<groupId>") {
                    g = t.trim_start_matches("<groupId>").trim_end_matches("</groupId>").to_string();
                } else if t.starts_with("<artifactId>") {
                    a = t.trim_start_matches("<artifactId>").trim_end_matches("</artifactId>").to_string();
                } else if t.starts_with("<scope>") {
                    scope = t.trim_start_matches("<scope>").trim_end_matches("</scope>").to_string();
                }
            }
        }

        if !normal.is_empty() {
            println!("Dependencies:");
            for d in &normal {
                println!("  - {}", d);
            }
        }
        if !test.is_empty() {
            println!("Test/Provided Dependencies:");
            for d in &test {
                println!("  - {}", d);
            }
        }
        }
    }
    Ok(())
}

// ─── CLI Entry ───────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() < 2 {
        eprintln!("Usage: pkg-checker <ecosystem> <package> [<maven-groupId>]");
        eprintln!("Ecosystems: crate, pip, npm, maven");
        process::exit(1);
    }

    let eco = args[0].as_str();
    let pkg = args[1].as_str();
    let mvn_group = args.get(2).map(|s| s.as_str());

    let result = match eco {
        "crate" | "rust" => check_crate(pkg).await,
        "pip" | "python" | "pypi" => check_pip(pkg).await,
        "npm" | "node" | "nodejs" => check_npm(pkg).await,
        "maven" | "java" | "mvn" => check_maven(pkg, mvn_group).await,
        _ => {
            eprintln!("Unknown ecosystem: {}. Use: crate, pip, npm, maven", eco);
            process::exit(1);
        }
    };

    if let Err(e) = result {
        eprintln!("Error: {}", e);
        process::exit(1);
    }
}

// ─── Tests ───────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_crate_serde() {
        let json = r#"{"crate":{"name":"tokio","max_version":"1.40.0","homepage":"https://tokio.rs","documentation":"https://docs.rs/tokio"},"versions":[]}"#;
        let meta: CrateMeta = serde_json::from_str(json).unwrap();
        assert_eq!(meta.crate_info.name, "tokio");
        assert_eq!(meta.crate_info.max_version, "1.40.0");
        assert_eq!(meta.crate_info.documentation, Some("https://docs.rs/tokio".to_string()));
    }

    #[tokio::test]
    async fn test_crate_deps_deserialize() {
        let json = r#"{"dependencies":[{"name":"pin-project-lite","req":"^0.2","kind":"normal"},{"name":"tokio-test","req":"^1","kind":"dev"}]}"#;
        let deps: CrateDeps = serde_json::from_str(json).unwrap();
        assert_eq!(deps.dependencies.len(), 2);
        assert_eq!(deps.dependencies[0].name, "pin-project-lite");
        assert_eq!(deps.dependencies[0].kind, Some("normal".to_string()));
        assert_eq!(deps.dependencies[1].kind, Some("dev".to_string()));
    }

    // ── live API tests (set RUST_TEST_LIVE=1 to run) ──────────────────────

    #[tokio::test]
    async fn test_crate_real() {
        if std::env::var("RUST_TEST_LIVE").is_err() {
            return;
        }
        let r = check_crate("serde").await;
        assert!(r.is_ok(), "check_crate(serde) failed: {:?}", r);
    }

    #[tokio::test]
    async fn test_pip_real() {
        if std::env::var("RUST_TEST_LIVE").is_err() {
            return;
        }
        let r = check_pip("requests").await;
        assert!(r.is_ok(), "check_pip(requests) failed: {:?}", r);
    }

    #[tokio::test]
    async fn test_npm_real() {
        if std::env::var("RUST_TEST_LIVE").is_err() {
            return;
        }
        let r = check_npm("express").await;
        assert!(r.is_ok(), "check_npm(express) failed: {:?}", r);
    }

    #[tokio::test]
    async fn test_maven_real() {
        if std::env::var("RUST_TEST_LIVE").is_err() {
            return;
        }
        let r = check_maven("gson", Some("com.google.code.gson")).await;
        assert!(r.is_ok(), "check_maven gson failed: {:?}", r);
    }

    #[tokio::test]
    async fn test_crate_not_found() {
        let r = check_crate("this-crate-does-not-exist-xyz-12345").await;
        assert!(r.is_err());
    }

    #[tokio::test]
    async fn test_pip_not_found() {
        let r = check_pip("this-package-does-not-exist-xyz-12345").await;
        assert!(r.is_err());
    }

    #[tokio::test]
    async fn test_npm_not_found() {
        let r = check_npm("this-npm-package-does-not-exist-xyz-12345").await;
        assert!(r.is_err());
    }
}
