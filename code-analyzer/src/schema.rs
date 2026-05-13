//! Canonical JSON data models.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Per-file analysis result.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Finding {
    pub file_path: String,
    pub feature_type: FeatureType,
    pub identifiers: Vec<String>,
    pub complexity_score: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub loc: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub nesting_depth: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub routes: Option<Vec<String>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub edges: Option<Vec<Edge>>,
}

/// Import/export relationship.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Edge {
    #[serde(rename = "type")]
    pub edge_type: String,
    pub name: String,
    pub source: String,
}

/// Feature classification.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum FeatureType {
    #[serde(rename = "Route")]
    Route,
    #[serde(rename = "Component")]
    Component,
    #[serde(rename = "Logic")]
    Logic,
}

impl std::fmt::Display for FeatureType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            FeatureType::Route => write!(f, "Route"),
            FeatureType::Component => write!(f, "Component"),
            FeatureType::Logic => write!(f, "Logic"),
        }
    }
}

/// Full E2E report.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Report {
    pub metadata: ReportMetadata,
    pub findings: Vec<Finding>,
    pub summary: Summary,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReportMetadata {
    pub target: String,
    pub languages: Vec<String>,
    pub total_files: usize,
    pub total_findings: usize,
    pub generated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Summary {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub avg_complexity: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_complexity: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub min_complexity: Option<u32>,
}

/// Token-optimized grouped output.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CondensedReport {
    pub metadata: CondensedMetadata,
    pub grouped: HashMap<String, FeatureGroup>,
    pub summary: CondensedSummary,
    pub total_files: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CondensedMetadata {
    pub target: String,
    pub languages: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FeatureGroup {
    pub identifiers: Vec<String>,
    pub files: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CondensedSummary {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub avg: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub min: Option<u32>,
}
