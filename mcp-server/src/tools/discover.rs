//! # Discover Resources Tool
//!
//! MCP tool that searches the local resource registry for paid resources
//! matching a query string. Performs case-insensitive substring matching
//! against resource names and descriptions.

use serde::{Deserialize, Serialize};

/// A paid resource entry from the registry.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Resource {
    pub id: String,
    pub name: String,
    pub contract_id: String,
    pub method: String,
    pub price: u64,
    pub description: String,
}

/// Load resources from the embedded registry JSON.
pub fn load_registry() -> Vec<Resource> {
    let registry_json = include_str!("../../../registry/resources.json");
    serde_json::from_str(registry_json).unwrap_or_default()
}

/// Search resources by query (case-insensitive substring match).
pub fn search_resources(query: &str) -> Vec<Resource> {
    let resources = load_registry();
    let query_lower = query.to_lowercase();

    resources
        .into_iter()
        .filter(|r| {
            r.name.to_lowercase().contains(&query_lower)
                || r.description.to_lowercase().contains(&query_lower)
                || r.id.to_lowercase().contains(&query_lower)
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_load_registry() {
        let resources = load_registry();
        assert!(
            !resources.is_empty(),
            "Registry should have at least one resource"
        );
    }

    #[test]
    fn test_search_resources() {
        let results = search_resources("weather");
        assert!(
            !results.is_empty(),
            "Should find weather resource"
        );
    }

    #[test]
    fn test_search_no_match() {
        let results = search_resources("nonexistent_resource_xyz");
        assert!(results.is_empty(), "Should find no resources");
    }
}
