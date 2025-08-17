.
├── bin
│   └── cloud-sql-proxy
├── config
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-312.pyc
│   │   └── settings.cpython-312.pyc
│   └── settings.py
├── customer_service_agent_app
│   ├── agent.py
│   ├── config
│   │   └── __init__.py
│   ├── database
│   │   └── __init__.py
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── agent.cpython-312.pyc
│   │   └── __init__.cpython-312.pyc
│   ├── repository
│   │   ├── customer_repository.py
│   │   ├── __init__.py
│   │   ├── knowledge_repository.py
│   │   ├── models.py
│   │   ├── priority_repository.py
│   │   ├── __pycache__
│   │   │   ├── customer_repository.cpython-312.pyc
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── knowledge_repository.cpython-312.pyc
│   │   │   ├── priority_repository.cpython-312.pyc
│   │   │   └── sentiment_repository.cpython-312.pyc
│   │   └── sentiment_repository.py
│   ├── scripts
│   │   └── __init__.py
│   └── subagents
│       ├── context_analyzer
│       │   ├── agent.py
│       │   ├── __init__.py
│       │   ├── __pycache__
│       │   │   ├── agent.cpython-312.pyc
│       │   │   ├── __init__.cpython-312.pyc
│       │   │   └── tools.cpython-312.pyc
│       │   └── tools.py
│       ├── __init__.py
│       ├── knowledge_agent
│       │   ├── agent.py
│       │   ├── __init__.py
│       │   ├── __pycache__
│       │   │   ├── agent.cpython-312.pyc
│       │   │   ├── __init__.cpython-312.pyc
│       │   │   └── tools.cpython-312.pyc
│       │   └── tools.py
│       ├── priority_agent
│       │   ├── agent.py
│       │   ├── __init__.py
│       │   ├── __pycache__
│       │   │   ├── agent.cpython-312.pyc
│       │   │   ├── __init__.cpython-312.pyc
│       │   │   └── tools.cpython-312.pyc
│       │   └── tools.py
│       ├── __pycache__
│       │   └── __init__.cpython-312.pyc
│       ├── response_synthesizer
│       │   ├── agent.py
│       │   ├── __init__.py
│       │   └── __pycache__
│       │       ├── agent.cpython-312.pyc
│       │       └── __init__.cpython-312.pyc
│       └── sentiment_agent
│           ├── agent.py
│           ├── __init__.py
│           ├── __pycache__
│           │   ├── agent.cpython-312.pyc
│           │   ├── __init__.cpython-312.pyc
│           │   └── tools.cpython-312.pyc
│           └── tools.py
├── docs
├── gcp-credentials.json
├── knowledge_mcp_server.py
├── knowledge_mcp_server_simple.py
├── knowledge_mcp_server_standalone.py
├── __pycache__
│   ├── customer_repository.cpython-312.pyc
│   ├── knowledge_mcp_server.cpython-312.pyc
│   └── mcp_server.cpython-312.pyc
├── README.md
├── scripts
│   ├── 00_setup_local_env.sh
│   ├── 01_setup_gcp_project.sh
│   ├── 02_setup_cloudsql.sh
│   ├── 03_run_proxy_and_init_db.sh
│   ├── connect_proxy.sh
│   ├── create_setup_scripts.py
│   ├── enable_pgvector.py
│   ├── init_database.py
│   ├── install_mcp_dependencies.sh
│   ├── project_structure.py
│   └── verify_environment.py
├── tests
│   ├── __init__.py
│   ├── test_context_analyzer.py
│   ├── test_full_agent_flow.py
│   └── test_vectors.py
├── tree_tfm_agentes.md
└── venv_tfm_agents

5177 directories, 43873 files
