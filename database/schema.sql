-- Fivoria AI Platform Database Schema
-- Separate AI metadata from existing marketplace tables

-- ============================================
-- MODEL REGISTRY
-- ============================================

CREATE TABLE ai_models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    architecture_type ENUM('dense', 'moe') NOT NULL,
    parameter_count BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_parameter_count (parameter_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ai_model_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_id INT NOT NULL,
    version VARCHAR(50) NOT NULL,
    architecture_config JSON NOT NULL,
    tokenizer_version VARCHAR(50),
    dataset_version VARCHAR(50),
    parameter_count BIGINT NOT NULL,
    status ENUM('development', 'training', 'evaluation', 'approved', 'staging', 'production', 'deprecated') DEFAULT 'development',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES ai_models(id) ON DELETE CASCADE,
    UNIQUE KEY uk_model_version (model_id, version),
    INDEX idx_status (status),
    INDEX idx_model_version (model_id, version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TRAINING RUNS
-- ============================================

CREATE TABLE ai_training_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL UNIQUE,
    model_version_id INT NOT NULL,
    dataset_version_id INT,
    gpu_cluster_id VARCHAR(100),
    config JSON NOT NULL,
    status ENUM('pending', 'running', 'paused', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    training_steps INT DEFAULT 0,
    consumed_tokens BIGINT DEFAULT 0,
    final_loss FLOAT,
    checkpoint_path VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (model_version_id) REFERENCES ai_model_versions(id) ON DELETE CASCADE,
    INDEX idx_run_id (run_id),
    INDEX idx_status (status),
    INDEX idx_model_version (model_version_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- CHECKPOINTS
-- ============================================

CREATE TABLE ai_training_checkpoints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    training_run_id INT NOT NULL,
    checkpoint_id VARCHAR(100) NOT NULL,
    step INT NOT NULL,
    consumed_tokens BIGINT NOT NULL,
    loss FLOAT,
    storage_path VARCHAR(500) NOT NULL,
    checksum VARCHAR(64),
    size_bytes BIGINT,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (training_run_id) REFERENCES ai_training_runs(id) ON DELETE CASCADE,
    UNIQUE KEY uk_training_checkpoint (training_run_id, checkpoint_id),
    INDEX idx_training_run (training_run_id),
    INDEX idx_step (step)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- DATASETS
-- ============================================

CREATE TABLE ai_datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    documents BIGINT NOT NULL,
    tokens BIGINT NOT NULL,
    languages JSON,
    quality_score FLOAT,
    license_status ENUM('verified', 'pending', 'rejected') DEFAULT 'pending',
    safety_status ENUM('clean', 'pending', 'flagged') DEFAULT 'pending',
    pii_status ENUM('filtered', 'pending', 'unfiltered') DEFAULT 'pending',
    mixture_config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_dataset_id (dataset_id),
    INDEX idx_version (version),
    INDEX idx_quality_score (quality_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ai_dataset_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    source_id VARCHAR(100) NOT NULL,
    provider VARCHAR(255),
    url TEXT,
    license VARCHAR(100),
    acquisition_date DATE,
    permission_status ENUM('verified', 'pending', 'rejected') DEFAULT 'pending',
    jurisdiction VARCHAR(100),
    allowed_uses JSON,
    restrictions TEXT,
    checksum VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES ai_datasets(id) ON DELETE CASCADE,
    INDEX idx_dataset (dataset_id),
    INDEX idx_source_id (source_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- EXPERIMENTS
-- ============================================

CREATE TABLE ai_experiments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    experiment_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_version_id INT,
    dataset_version_id INT,
    config JSON NOT NULL,
    status ENUM('running', 'completed', 'failed') DEFAULT 'running',
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    results JSON,
    git_commit VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_version_id) REFERENCES ai_model_versions(id) ON DELETE SET NULL,
    INDEX idx_experiment_id (experiment_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- EVALUATION
-- ============================================

CREATE TABLE ai_evaluations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_version_id INT NOT NULL,
    evaluation_id VARCHAR(100) NOT NULL UNIQUE,
    benchmark_name VARCHAR(100) NOT NULL,
    benchmark_version VARCHAR(50),
    score FLOAT,
    metrics JSON,
    dataset_version VARCHAR(50),
    configuration JSON,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_version_id) REFERENCES ai_model_versions(id) ON DELETE CASCADE,
    UNIQUE KEY uk_model_benchmark (model_version_id, benchmark_name, evaluation_id),
    INDEX idx_model_version (model_version_id),
    INDEX idx_benchmark (benchmark_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- BENCHMARKS
-- ============================================

CREATE TABLE ai_benchmarks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    version VARCHAR(50),
    dataset_size INT,
    evaluation_script_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- MODEL DEPLOYMENTS
-- ============================================

CREATE TABLE ai_model_deployments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_version_id INT NOT NULL,
    deployment_id VARCHAR(100) NOT NULL UNIQUE,
    environment ENUM('staging', 'production') NOT NULL,
    endpoint_url VARCHAR(500),
    gpu_count INT,
    quantization VARCHAR(20),
    status ENUM('deploying', 'active', 'inactive', 'failed') DEFAULT 'deploying',
    deployed_at TIMESTAMP NULL,
    undeployed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_version_id) REFERENCES ai_model_versions(id) ON DELETE CASCADE,
    INDEX idx_model_version (model_version_id),
    INDEX idx_environment (environment),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- TOOL REGISTRY
-- ============================================

CREATE TABLE ai_tool_registry (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tool_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    schema JSON NOT NULL,
    implementation_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    requires_sandbox BOOLEAN DEFAULT FALSE,
    timeout_seconds INT DEFAULT 30,
    rate_limit_per_minute INT DEFAULT 60,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- AGENT RUNS
-- ============================================

CREATE TABLE ai_agent_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL UNIQUE,
    user_id INT,
    session_id VARCHAR(100),
    agent_type VARCHAR(50),
    query TEXT,
    plan JSON,
    tool_calls JSON,
    result TEXT,
    tokens_used INT,
    latency_ms INT,
    status ENUM('running', 'completed', 'failed') DEFAULT 'running',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- MEMORY METADATA
-- ============================================

CREATE TABLE ai_memory_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    memory_type ENUM('short_term', 'long_term', 'semantic', 'factual', 'episodic') NOT NULL,
    storage_key VARCHAR(255),
    expires_at TIMESTAMP NULL,
    encryption_required BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_type (user_id, memory_type),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- RAG DOCUMENTS
-- ============================================

CREATE TABLE ai_rag_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    document_id VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(100),
    title VARCHAR(500),
    content TEXT,
    embedding_vector_id VARCHAR(100),
    metadata JSON,
    chunk_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_source (source_type, source_id),
    INDEX idx_document_id (document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- AI USAGE
-- ============================================

CREATE TABLE ai_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    model_version_id INT,
    request_type VARCHAR(50) NOT NULL,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    latency_ms INT,
    status ENUM('success', 'error') DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_version_id) REFERENCES ai_model_versions(id) ON DELETE SET NULL,
    INDEX idx_user_date (user_id, created_at),
    INDEX idx_model_version (model_version_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- AUDIT LOGS
-- ============================================

CREATE TABLE ai_audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_action (user_id, action),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- GPU CLUSTERS
-- ============================================

CREATE TABLE ai_gpu_clusters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cluster_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    gpu_type VARCHAR(50),
    gpu_count INT,
    cpu_count INT,
    memory_gb INT,
    interconnect VARCHAR(50),
    status ENUM('active', 'maintenance', 'offline') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- SECURITY
-- ============================================

CREATE TABLE ai_api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100),
    permissions JSON,
    rate_limit_per_minute INT DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP NULL,
    last_used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_api_key (api_key_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Composite indexes for common queries
CREATE INDEX idx_training_runs_status_time ON ai_training_runs(status, start_time);
CREATE INDEX idx_evaluations_model_benchmark ON ai_evaluations(model_version_id, benchmark_name);
CREATE INDEX idx_usage_user_model ON ai_usage(user_id, model_version_id);
CREATE INDEX idx_rag_source_created ON ai_rag_documents(source_type, created_at);

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View for active model deployments
CREATE VIEW v_active_deployments AS
SELECT 
    md.id,
    m.name AS model_name,
    mv.version AS model_version,
    md.environment,
    md.endpoint_url,
    md.gpu_count,
    md.quantization,
    md.deployed_at
FROM ai_model_deployments md
JOIN ai_model_versions mv ON md.model_version_id = mv.id
JOIN ai_models m ON mv.model_id = m.id
WHERE md.status = 'active';

-- View for training progress
CREATE VIEW v_training_progress AS
SELECT 
    tr.id,
    tr.run_id,
    m.name AS model_name,
    mv.version AS model_version,
    tr.status,
    tr.training_steps,
    tr.consumed_tokens,
    tr.final_loss,
    tr.start_time,
    TIMESTAMPDIFF(SECOND, tr.start_time, NOW()) AS duration_seconds
FROM ai_training_runs tr
JOIN ai_model_versions mv ON tr.model_version_id = mv.id
JOIN ai_models m ON mv.model_id = m.id
WHERE tr.status IN ('running', 'paused');

-- View for model evaluation summary
CREATE VIEW v_model_evaluation_summary AS
SELECT 
    m.name AS model_name,
    mv.version AS model_version,
    e.benchmark_name,
    e.score,
    e.evaluated_at
FROM ai_evaluations e
JOIN ai_model_versions mv ON e.model_version_id = mv.id
JOIN ai_models m ON mv.model_id = m.id
ORDER BY e.evaluated_at DESC;
