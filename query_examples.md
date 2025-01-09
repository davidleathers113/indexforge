# Vector Database Query Examples

This document demonstrates how to interact with the vector database through different query patterns. Each example includes:
1. A **natural language query** (user input)
2. Both **vector query** and **SQL-like query** syntax
3. **Expected output** with detailed explanation

## 1. Document Discovery Queries

### Find Similar Technical Specifications
```
Natural Query:
"Find all technical specifications related to authentication implementation"

Vector Query:
{
  "type": "similarity_search",
  "content_filter": {
    "content_type": "tech_spec",
    "lifecycle_stage": "implementation"
  },
  "vector_query": {
    "text": "authentication system implementation details",
    "model": "text-embedding-ada-002",
    "k_nearest": 5,
    "min_similarity": 0.7
  }
}

SQL-Like Syntax:
SELECT docs
FROM vector_db
WHERE category_name = "documentation"
  AND content_type = "tech_spec"
  AND lifecycle_stage = "implementation"
  AND vector_similarity(
    content_embedding,
    embed("authentication system implementation details")
  ) >= 0.7
ORDER BY similarity DESC
LIMIT 5;

Expected Output:
[
  {
    "document_id": "tech_spec_auth_123",
    "title": "Authentication System Technical Specification",
    "similarity": 0.89,
    "metadata": {
      "last_modified": "2024-01-15",
      "author": "security_team",
      "status": "approved"
    },
    "relevant_sections": [
      "OAuth Implementation",
      "MFA Architecture"
    ]
  }
]
```

### Review Cycle Analysis
```
Natural Query:
"Which documentation items have missed their review cycle?"

Vector Query:
{
  "type": "review_cycle_check",
  "filters": {
    "document_types": ["tech_spec", "prd", "getting_started"],
    "review_status": "overdue"
  },
  "temporal": {
    "review_cycle_field": "review_cycle",
    "last_review_field": "last_reviewed_date"
  }
}

SQL-Like Syntax:
SELECT docs
FROM vector_db
WHERE category_name = "documentation"
  AND (
    (review_cycle = "weekly" AND last_reviewed_date < (CURRENT_DATE - INTERVAL '7' DAY))
    OR
    (review_cycle = "bi-weekly" AND last_reviewed_date < (CURRENT_DATE - INTERVAL '14' DAY))
    OR
    (review_cycle = "monthly" AND last_reviewed_date < (CURRENT_DATE - INTERVAL '30' DAY))
  )
ORDER BY last_reviewed_date ASC;

Expected Output:
{
  "overdue_documents": [
    {
      "document_id": "tech_spec_456",
      "title": "Payment Gateway Integration",
      "review_cycle": "weekly",
      "last_reviewed": "2024-01-01",
      "days_overdue": 14,
      "owner": "integration_team"
    }
  ],
  "summary": {
    "total_overdue": 5,
    "by_type": {
      "tech_spec": 2,
      "prd": 2,
      "getting_started": 1
    }
  }
}
```

### Cross-Document Relationship Search
```
Natural Query:
"Show all documents and meetings related to the payment processing feature"

Vector Query:
{
  "type": "graph_traversal",
  "start_points": {
    "semantic_match": "payment processing feature",
    "content_types": ["tech_spec", "prd", "meeting_notes"]
  },
  "relationship_filter": {
    "types": ["reference", "mention", "dependency"],
    "max_depth": 2
  },
  "temporal_order": "chronological"
}

Expected Output:
{
  "documents": [
    {
      "type": "prd",
      "title": "Payment Processing Requirements",
      "date": "2024-01-01",
      "relationships": ["tech_spec_123", "meeting_456"]
    },
    {
      "type": "tech_spec",
      "title": "Stripe Integration Architecture",
      "date": "2024-01-15",
      "relationships": ["meeting_789"]
    }
  ],
  "meetings": [
    {
      "type": "planning",
      "title": "Payment Feature Kickoff",
      "date": "2024-01-10",
      "key_decisions": [...]
    }
  ]
}
```

## 2. Meeting Intelligence Queries

### Action Item Tracking
```
Natural Query:
"Show all open action items from weekly sync meetings in the last month"

Vector Query:
{
  "type": "filtered_semantic_search",
  "temporal_filter": {
    "meeting_type": "weekly",
    "date_range": "last_30_days"
  },
  "content_filter": {
    "field": "action_items",
    "status": "open"
  },
  "aggregation": "by_owner"
}

Expected Output:
{
  "action_items": {
    "by_owner": {
      "john_doe": [
        {
          "item": "Update authentication flow diagram",
          "due_date": "2024-02-01",
          "meeting_source": "Team Weekly @Jan 15, 2024",
          "priority": "high"
        }
      ],
      "jane_smith": [
        // ... other action items
      ]
    }
  }
}
```

### Meeting Pattern Analysis
```
Natural Query:
"What are the most discussed topics in standup meetings where the authentication feature was mentioned?"

Vector Query:
{
  "type": "semantic_aggregation",
  "filter": {
    "meeting_type": "standup",
    "semantic_match": "authentication feature"
  },
  "analysis": {
    "topic_extraction": true,
    "frequency_analysis": true,
    "time_window": "last_90_days"
  }
}

Expected Output:
{
  "top_topics": [
    {
      "topic": "MFA Implementation",
      "frequency": 15,
      "related_terms": ["2FA", "security", "user flow"],
      "trend": "increasing"
    },
    // ... other topics
  ],
  "timeline": {
    "topic_evolution": [...],
    "key_meetings": [...]
  }
}
```

## 3. Project Progress Queries

### Development Stage Analysis
```
Natural Query:
"Show the progress of all features currently in implementation phase"

Vector Query:
{
  "type": "lifecycle_analysis",
  "filter": {
    "lifecycle_stage": "implementation",
    "document_types": ["tech_spec", "prd"]
  },
  "relationships": {
    "include": ["dependencies", "blockers"],
    "status_tracking": true
  }
}

Expected Output:
{
  "features": [
    {
      "name": "Payment Processing",
      "progress": 0.75,
      "status": {
        "implementation": "in_progress",
        "documentation": "complete",
        "testing": "pending"
      },
      "blockers": [
        {
          "description": "Awaiting API credentials",
          "owner": "security_team"
        }
      ]
    }
  ]
}
```

## 4. Knowledge Graph Queries

### Impact Analysis
```
Natural Query:
"What would be affected if we change the authentication service?"

Vector Query:
{
  "type": "impact_analysis",
  "target": {
    "semantic_match": "authentication service",
    "document_types": ["tech_spec"]
  },
  "relationship_traverse": {
    "types": ["dependency", "integration"],
    "max_depth": 3
  }
}

Expected Output:
{
  "affected_components": [
    {
      "name": "Payment Processing",
      "impact_level": "high",
      "dependency_path": ["auth_service", "user_session", "payment_flow"],
      "relevant_docs": [...]
    }
  ],
  "required_updates": [
    {
      "document_type": "tech_spec",
      "title": "Payment Flow Architecture",
      "sections": ["Authentication Integration"]
    }
  ]
}
```

## 5. Temporal Analysis Queries

### Decision Timeline
```
Natural Query:
"Show the evolution of decisions about the payment processing feature"

Vector Query:
{
  "type": "temporal_analysis",
  "subject": {
    "semantic_match": "payment processing",
    "document_types": ["meeting_notes", "prd", "tech_spec"]
  },
  "timeline": {
    "order": "chronological",
    "group_by": "decision_type",
    "include_context": true
  }
}

Expected Output:
{
  "timeline": [
    {
      "date": "2024-01-01",
      "event_type": "initial_planning",
      "document": "PRD: Payment Processing",
      "key_decisions": [
        {
          "decision": "Use Stripe as payment processor",
          "rationale": "Better API documentation and support",
          "stakeholders": ["product_team", "engineering"]
        }
      ]
    }
  ],
  "decision_flow": {
    "visualization": "decision_tree",
    "key_milestones": [...]
  }
}
```

## 6. Practical Day-to-Day Queries

### Action Item Status Check
```
Natural Query:
"Show me all overdue action items assigned to the security team"

Vector Query:
{
  "type": "action_item_search",
  "filters": {
    "assignee": "security_team",
    "status": "overdue"
  },
  "include_context": true
}

SQL-Like Syntax:
SELECT action_items, source_docs
FROM vector_db
WHERE action_items->assignee = "security_team"
  AND action_items->due_date < CURRENT_DATE
  AND action_items->status != "completed"
ORDER BY action_items->due_date ASC;

Expected Output:
{
  "overdue_items": [
    {
      "item": "Complete security audit for payment system",
      "due_date": "2024-01-15",
      "days_overdue": 5,
      "source": {
        "type": "meeting",
        "title": "Security Planning Session",
        "date": "2024-01-08"
      },
      "related_docs": [
        {
          "type": "tech_spec",
          "title": "Payment System Security Architecture"
        }
      ]
    }
  ]
}
```

## 7. Business Restructuring Queries

### Historical Pattern Analysis
```
Natural Query:
"What are the most common challenges mentioned in team communications over the past year?"

Vector Query:
{
  "type": "pattern_analysis",
  "sources": ["email", "chat", "meetings", "docs"],
  "semantic_match": "challenges OR problems OR issues OR blockers",
  "time_range": "last_12_months",
  "aggregation": {
    "group_by": "topic",
    "min_frequency": 3,
    "include_context": true
  }
}

SQL-Like Syntax:
WITH communication_items AS (
  SELECT content, source_type, timestamp,
         extract_topics(content) as topics
  FROM vector_db
  WHERE timestamp > NOW() - INTERVAL '1 year'
    AND source_type IN ('email', 'chat', 'meeting', 'document')
    AND vector_similarity(
      content_embedding,
      embed("challenges problems issues blockers")
    ) > 0.7
)
SELECT
  topic,
  COUNT(*) as frequency,
  array_agg(DISTINCT source_type) as sources,
  array_agg(content) as context_samples
FROM communication_items
CROSS JOIN UNNEST(topics) as topic
GROUP BY topic
HAVING COUNT(*) >= 3
ORDER BY frequency DESC;

Expected Output:
{
  "recurring_challenges": [
    {
      "topic": "Communication Gaps",
      "frequency": 15,
      "sources": ["email", "meetings", "chat"],
      "context": [
        {
          "source": "team_meeting",
          "date": "2023-08-15",
          "snippet": "Team expressed confusion about project priorities..."
        },
        {
          "source": "email_thread",
          "date": "2023-09-22",
          "snippet": "Missing key information about client requirements..."
        }
      ],
      "trend": "decreasing"
    }
  ],
  "impact_areas": {
    "high": ["project_coordination", "information_flow"],
    "medium": ["tool_adoption", "process_adherence"],
    "low": ["technical_issues"]
  }
}
```

### Team Structure Analysis
```
Natural Query:
"Show me the informal communication and collaboration patterns between teams"

Vector Query:
{
  "type": "network_analysis",
  "data_sources": {
    "email": {
      "fields": ["from", "to", "cc"],
      "exclude": ["external_domains"]
    },
    "chat": {
      "fields": ["participants", "mentions"],
      "channels": ["team_*", "project_*"]
    },
    "documents": {
      "fields": ["collaborators", "commenters"]
    }
  },
  "time_range": "last_6_months",
  "analysis": {
    "graph_metrics": ["centrality", "clustering"],
    "identify_bridges": true
  }
}

Expected Output:
{
  "team_interactions": {
    "strong_connections": [
      {
        "teams": ["product", "engineering"],
        "interaction_score": 0.85,
        "primary_channels": ["slack", "product_docs"],
        "key_collaborators": ["jane_doe", "john_smith"]
      }
    ],
    "weak_connections": [
      {
        "teams": ["marketing", "engineering"],
        "interaction_score": 0.23,
        "recommendation": "Consider regular sync meetings"
      }
    ],
    "bridge_roles": [
      {
        "person": "alice_jones",
        "role": "product_manager",
        "connects_teams": ["design", "engineering", "sales"],
        "interaction_types": ["requirements", "feedback", "coordination"]
      }
    ]
  }
}
```

## 8. Cross-Platform Knowledge Queries

### Topic Threading
```
Natural Query:
"Show me how the discussion about 'customer onboarding automation' evolved across platforms"

Vector Query:
{
  "type": "topic_evolution",
  "subject": "customer onboarding automation",
  "sources": {
    "notion": ["docs", "meetings"],
    "email": ["threads", "attachments"],
    "chat": ["channels", "direct_messages"],
    "google_docs": ["documents", "comments"]
  },
  "analysis": {
    "chronological": true,
    "identify_decisions": true,
    "track_stakeholders": true
  }
}

Expected Output:
{
  "topic_evolution": [
    {
      "phase": "ideation",
      "date_range": "2023-06-01 to 2023-06-15",
      "sources": [
        {
          "platform": "slack",
          "channel": "product-ideas",
          "key_points": ["Initial discussion about automation needs"]
        },
        {
          "platform": "notion",
          "document": "Brainstorm: Customer Onboarding",
          "key_points": ["Documented requirements", "Initial scope"]
        }
      ]
    },
    {
      "phase": "planning",
      "date_range": "2023-06-16 to 2023-06-30",
      "key_decisions": [
        {
          "decision": "Use Zapier for automation",
          "context": {
            "platform": "google_docs",
            "document": "Technical Architecture",
            "discussion_thread": "..."
          }
        }
      ]
    }
  ]
}
```

## 9. Migration Intelligence Queries

### Content Restructuring Analysis
```
Natural Query:
"Suggest an optimal structure for our new Notion workspace based on current usage patterns"

Vector Query:
{
  "type": "structure_analysis",
  "sources": {
    "notion": {
      "analyze": ["page_hierarchy", "cross_links", "access_patterns"]
    },
    "google_docs": {
      "analyze": ["folder_structure", "sharing_patterns"]
    },
    "email": {
      "analyze": ["attachment_organization", "thread_topics"]
    }
  },
  "optimization_goals": [
    "reduce_navigation_depth",
    "group_related_content",
    "optimize_access_patterns"
  ]
}

Expected Output:
{
  "recommended_structure": {
    "top_level": [
      {
        "name": "Client Projects",
        "rationale": "High access frequency, clear ownership",
        "suggested_substructure": [
          {
            "name": "Active Projects",
            "content_types": ["briefs", "timelines", "meetings"],
            "access_patterns": {
              "primary_teams": ["product", "client_success"],
              "frequency": "daily"
            }
          }
        ]
      }
    ],
    "content_relationships": [
      {
        "content_cluster": "Onboarding Materials",
        "current_locations": [
          "Google Drive/Training/",
          "Notion/Guidelines/",
          "Email/Templates/"
        ],
        "suggested_consolidation": {
          "location": "Notion/Client Success/Onboarding/",
          "structure": "..."
        }
      }
    ]
  }
}
```

## 8. Index-Optimized Queries

### Vector Index (HNSW) Search
```
Natural Query:
"Find documents semantically similar to this project proposal, but only from the last month"

Vector Query:
{
  "type": "vector_similarity_search",
  "vector_config": {
    "index": "hnsw",
    "ef_search": 100,
    "space_type": "cosine",
    "min_similarity": 0.75
  },
  "filters": {
    "timestamp_utc": {
      "gte": "now-30d"
    }
  },
  "input_text": "Project proposal content here...",
  "limit": 10
}

Expected Output:
{
  "similar_documents": [
    {
      "doc_id": "proposal_123",
      "similarity_score": 0.92,
      "metadata": {
        "title": "Q4 Marketing Initiative",
        "timestamp_utc": "2024-01-15T10:30:00Z",
        "topic_label": "marketing_strategy"
      }
    }
  ],
  "query_stats": {
    "search_time_ms": 25,
    "nodes_visited": 150
  }
}
```

### Compound Index Query
```
Natural Query:
"Find all technical documentation about authentication that was updated this week"

Vector Query:
{
  "type": "hybrid_search",
  "use_index": "content_search",
  "filters": {
    "content_classification": {
      "topic_label": "technical",
      "auto_tags": ["authentication", "security"]
    },
    "metadata.timestamp_utc": {
      "gte": "now-7d"
    }
  },
  "semantic_query": "authentication implementation details",
  "boost_factors": {
    "topic_relevance": 0.3,
    "vector_similarity": 0.7
  }
}

Expected Output:
{
  "matching_documents": [
    {
      "doc_id": "auth_spec_789",
      "combined_score": 0.88,
      "scores": {
        "topic_relevance": 0.95,
        "vector_similarity": 0.85
      },
      "metadata": {
        "title": "OAuth2 Implementation Guide",
        "last_modified": "2024-01-20T15:45:00Z"
      }
    }
  ]
}
```

### Materialized View Query
```
Natural Query:
"Show me the main topic clusters in our technical documentation"

Vector Query:
{
  "type": "topic_cluster_analysis",
  "use_view": "topic_clusters",
  "min_cluster_size": 3,
  "min_similarity": 0.6,
  "aggregation": {
    "group_by": "content_classification.topic_label",
    "metrics": ["document_count", "average_similarity"]
  }
}

Expected Output:
{
  "topic_clusters": [
    {
      "topic": "authentication",
      "document_count": 15,
      "average_similarity": 0.82,
      "key_documents": [
        {
          "title": "Auth Service Architecture",
          "doc_id": "auth_123"
        }
      ],
      "related_topics": ["security", "user_management"]
    }
  ],
  "cluster_stats": {
    "total_clusters": 8,
    "avg_cluster_size": 12
  }
}
```

### Graph Index Query
```
Natural Query:
"Show me how our payment processing documentation is connected across platforms"

Vector Query:
{
  "type": "graph_traversal",
  "use_index": "relationship_graph",
  "start_node": {
    "doc_id": "payment_processing_main",
    "platform": "notion"
  },
  "traversal_config": {
    "max_depth": 3,
    "relationship_types": ["mentioned_documents", "linked_documents"],
    "min_weight": 0.5
  }
}

Expected Output:
{
  "document_graph": {
    "nodes": [
      {
        "id": "payment_processing_main",
        "platform": "notion",
        "type": "technical_spec"
      }
    ],
    "edges": [
      {
        "from": "payment_processing_main",
        "to": "stripe_integration_guide",
        "weight": 0.85,
        "type": "referenced_in"
      }
    ]
  },
  "graph_metrics": {
    "centrality_score": 0.75,
    "connection_strength": "high"
  }
}
```

### Temporal Index Query
```
Natural Query:
"Show me the evolution of our API documentation over the last quarter"

Vector Query:
{
  "type": "time_series_analysis",
  "use_index": "temporal",
  "filters": {
    "content_classification.topic_label": "api_documentation",
    "time_range": {
      "start": "now-90d",
      "end": "now",
      "interval": "1w"
    }
  },
  "metrics": [
    "document_count",
    "update_frequency",
    "content_changes"
  ]
}

Expected Output:
{
  "timeline": [
    {
      "period": "2024-W01",
      "metrics": {
        "document_count": 25,
        "new_documents": 3,
        "updated_documents": 8,
        "major_changes": [
          {
            "doc_id": "api_v2_spec",
            "change_type": "version_update"
          }
        ]
      }
    }
  ],
  "trend_analysis": {
    "update_frequency": "increasing",
    "content_stability": "high"
  }
}
```

### Hybrid Search Query
```
Natural Query:
"Find discussions about performance optimization in both documentation and chat channels"

Vector Query:
{
  "type": "cross_platform_search",
  "use_indexes": ["full_text", "vector_indexes"],
  "query": {
    "text": "performance optimization techniques",
    "vector_embedding": "[1536 dimensions]"
  },
  "platforms": ["notion", "slack", "google_docs"],
  "ranking": {
    "text_match_weight": 0.3,
    "vector_similarity_weight": 0.7,
    "recency_boost": true
  }
}

Expected Output:
{
  "results": [
    {
      "source": {
        "platform": "notion",
        "type": "technical_doc",
        "id": "perf_opt_guide"
      },
      "relevance": {
        "combined_score": 0.89,
        "text_match": 0.92,
        "vector_similarity": 0.87
      },
      "context": {
        "title": "Performance Optimization Guide",
        "snippet": "Implementing caching strategies for..."
      }
    },
    {
      "source": {
        "platform": "slack",
        "type": "thread",
        "channel": "engineering"
      },
      "relevance": {
        "combined_score": 0.82,
        "text_match": 0.75,
        "vector_similarity": 0.85
      },
      "context": {
        "message_preview": "We should consider using..."
      }
    }
  ],
  "search_metadata": {
    "total_results": 15,
    "search_time_ms": 150,
    "indexes_used": ["full_text", "hnsw"]
  }
}
```