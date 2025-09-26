# 🚀 Auto Documentation Generation System

An intelligent system that automatically analyzes your codebase and generates comprehensive documentation, with specialized support for AI/ML pipelines.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

## 🌟 Features

- **🔍 Intelligent Code Analysis**: AST-based Python code analysis with complexity metrics
- **🤖 AI/ML Pipeline Detection**: Specialized analysis for machine learning components
- **📚 Comprehensive Documentation**: Generates multiple documentation sections automatically
- **📊 Visual Diagrams**: Architecture diagrams and data flow visualizations
- **🗄️ Supabase Integration**: Complete data logging, monitoring, and debug interface
- **🔄 CI/CD Integration**: GitHub Actions workflow for automated documentation updates
- **🎨 Beautiful Output**: MkDocs Material theme with modern UI
- **⚡ Fast & Efficient**: Optimized for large codebases

## 📋 Generated Documentation

The system automatically generates:

- **📖 Project Overview**: High-level project statistics and summary
- **🏗️ Architecture Documentation**: System design and component relationships
- **📋 API Reference**: Detailed function and class documentation
- **👥 Onboarding Guide**: New developer getting-started guide
- **🤖 AI/ML Documentation**: Machine learning models and pipelines (if detected)
- **📊 Code Quality Reports**: Complexity analysis and metrics

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd auto_doc_generator

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Basic Usage

```bash
# Analyze current directory and generate documentation
python src/main.py --analyze --generate

# Analyze, generate, and build MkDocs site
python src/main.py --analyze --generate --build

# Serve documentation locally
python src/main.py --serve

# Analyze specific repository
python src/main.py --repo /path/to/your/project --analyze --generate
```

### Docker Usage

```bash
# Build Docker image
docker build -t auto-doc-generator .

# Run analysis on your project
docker run -v /path/to/your/project:/app/source -v /path/to/output:/app/docs auto-doc-generator --repo /app/source
```

## 📁 Project Structure

```
auto_doc_generator/
├── src/
│   ├── analyzers/
│   │   ├── code_analyzer.py      # Core code analysis
│   │   └── ai_pipeline_analyzer.py # AI/ML detection
│   ├── generators/
│   │   ├── markdown_generator.py # Documentation generation
│   │   └── diagram_generator.py  # Visual diagram creation
│   ├── supabase_integration.py  # Supabase logging & storage
│   ├── debug_interface.py       # Web debug interface
│   └── main.py                   # Main entry point
├── config/
│   ├── doc_config.yaml          # Main configuration
│   └── analysis_rules.yaml      # Analysis rules
├── templates/
│   ├── base_template.md         # Base documentation template
│   ├── architecture_template.md # Architecture documentation
│   ├── api_template.md          # API reference template
│   └── onboarding_template.md   # Onboarding guide template
├── .github/workflows/
│   └── auto-doc.yml             # GitHub Actions workflow
├── docs/                        # Generated documentation output
├── setup_supabase.py            # Supabase setup script
├── supabase_setup.sql           # Complete database setup (handles all scenarios)
├── start_debug_server.py        # Debug interface launcher
├── Dockerfile                   # Container definition
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## ⚙️ Configuration

### Basic Configuration (`config/doc_config.yaml`)

```yaml
analysis:
  include_patterns:
    - "*.py"
    - "*.js"
    - "*.ts"
  exclude_patterns:
    - "*/tests/*"
    - "*/__pycache__/*"
  
  ai_analysis:
    detect_frameworks: true
    analyze_pipelines: true
    generate_flow_diagrams: true

generation:
  output_format: "mkdocs"
  theme: "material"
  include_diagrams: true
  include_api_docs: true

deployment:
  target: "github_pages"
  auto_deploy: true
```

### Analysis Rules (`config/analysis_rules.yaml`)

```yaml
complexity_thresholds:
  cyclomatic:
    low: 5
    medium: 10
    high: 15

code_patterns:
  ai_pipeline:
    - "class.*Pipeline"
    - "def.*train"
    - "def.*predict"
```

## 🗄️ Supabase Integration

The system includes comprehensive Supabase integration for logging, data storage, and monitoring of the documentation generation process.

### Features

- **📊 Analysis Tracking**: Complete analysis results storage
- **🤖 LLM Logging**: All AI/LLM interactions with metrics
- **🎯 Vector Embeddings**: Code embeddings with pgvector for fast semantic search
- **🔬 Quality Assessments**: Module quality metrics and insights
- **📚 Documentation Tracking**: Generation metadata and results
- **🔍 Debug Interface**: Web-based monitoring dashboard

### Quick Setup

1. **Create Supabase Project**:
   - Go to [supabase.com](https://supabase.com) and create a new project
   - Note your project URL and anon key

2. **Set Environment Variables**:
   ```bash
   export SUPABASE_URL='https://your-project-ref.supabase.co'
   export SUPABASE_ANON_KEY='your-supabase-anon-key'
   ```

3. **Run Setup Script**:
   ```bash
   python setup_supabase.py
   ```

4. **Execute Database Schema**:
   - Copy contents of `supabase_setup.sql` and execute in Supabase SQL Editor
   - This single file handles both new setups and existing installations automatically

### Database Tables

The system creates 6 tables for comprehensive data storage:

| Table | Purpose |
|-------|---------|
| `analysis_steps` | Track each step of the analysis process |
| `llm_interactions` | Log all AI/LLM requests and responses |
| `vector_embeddings` | Store code embeddings using pgvector for fast semantic search |
| `quality_assessments` | Module quality metrics and LLM insights |
| `complete_analysis_results` | Full analysis data (code, AI, quality) |
| `documentation_generations` | Documentation generation tracking |

### Debug Interface

Monitor your data with the web-based debug interface:

```bash
# Start debug server
python start_debug_server.py

# Visit dashboard
open http://localhost:5001
```

**Available Endpoints**:
- `/api/database-stats` - Database statistics
- `/api/llm-interactions` - Recent AI interactions
- `/api/analysis-steps` - Analysis step history
- `/api/complete-analysis-results` - Full analysis data
- `/api/documentation-generations` - Documentation tracking
- `/api/vector-embeddings/search` - Semantic code search

### Configuration

Add Supabase configuration to your `documentor.yaml`:

```yaml
supabase:
  enabled: true
  url: ${SUPABASE_URL}
  key: ${SUPABASE_ANON_KEY}

# Optional: Customize logging behavior
logging:
  supabase:
    log_analysis_steps: true
    log_llm_interactions: true
    log_quality_assessments: true
    log_complete_results: true
    log_documentation: true
```

### Usage with Analysis

The system automatically logs data when Supabase is configured:

```bash
# Run analysis with Supabase logging
python -m auto_doc_generator.main --analyze --generate

# Start debug interface to monitor
python start_debug_server.py
```

### Data Retention

- **Development**: Data stored indefinitely
- **Production**: Consider implementing data retention policies
- **Privacy**: All data stored in your Supabase instance

For detailed setup instructions, see [SUPABASE_INTEGRATION.md](SUPABASE_INTEGRATION.md).

## 🔄 CI/CD Integration

### GitHub Actions

The system includes a pre-configured GitHub Actions workflow:

1. **Automatic Triggers**: Runs on push to main branch and merged PRs
2. **Documentation Generation**: Analyzes code and generates docs
3. **GitHub Pages Deployment**: Automatically deploys to GitHub Pages
4. **Quality Checks**: Lints documentation and runs completeness checks

### Setup Steps

1. Copy `.github/workflows/auto-doc.yml` to your repository
2. Enable GitHub Pages in repository settings
3. Push changes to trigger the workflow
4. Documentation will be available at `https://username.github.io/repository-name/`

## 🛠️ Advanced Usage

### Custom Analysis

```python
from src.analyzers.code_analyzer import CodeAnalyzer
from src.analyzers.ai_pipeline_analyzer import AIPipelineAnalyzer

# Initialize analyzers
code_analyzer = CodeAnalyzer("/path/to/project")
ai_analyzer = AIPipelineAnalyzer()

# Perform analysis
code_results = code_analyzer.analyze_codebase()
ai_results = ai_analyzer.analyze_ai_components("/path/to/project")
```

### Custom Documentation Generation

```python
from src.generators.markdown_generator import MarkdownGenerator

# Initialize generator
generator = MarkdownGenerator("templates", "output")

# Generate specific documentation
docs = generator.generate_all_documentation(code_results, ai_results)
generator.save_documentation(docs)
```

## 🎯 AI/ML Support

The system provides specialized analysis for:

- **🤖 Model Detection**: Identifies ML models, classifiers, and regressors
- **⚡ Pipeline Analysis**: Detects data processing pipelines
- **📈 Training Scripts**: Finds model training functions
- **🔮 Inference Endpoints**: Locates prediction/inference code
- **📊 Experiment Tracking**: Detects MLflow, WandB, TensorBoard usage
- **🗄️ Data Sources**: Identifies data loading and processing patterns

### Supported Frameworks

- TensorFlow/Keras
- PyTorch
- Scikit-learn
- Pandas/NumPy
- MLflow
- Weights & Biases (WandB)
- XGBoost/LightGBM
- Hugging Face Transformers

## 📊 Code Quality Metrics

The system analyzes:

- **Cyclomatic Complexity**: Function complexity scoring
- **Maintainability Index**: Code maintainability metrics
- **Halstead Metrics**: Software complexity measures
- **Dependency Analysis**: Module interdependencies
- **Architecture Patterns**: Design pattern detection

## 🔧 Troubleshooting

### Common Issues

**Issue**: Import errors when running analysis
```bash
# Solution: Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python src/main.py --analyze --generate
```

**Issue**: MkDocs not found
```bash
# Solution: Install MkDocs
pip install mkdocs mkdocs-material
```

**Issue**: Diagrams library errors
```bash
# Solution: Install system dependencies
sudo apt-get install graphviz graphviz-dev
pip install diagrams
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Lint code
flake8 src/
```

## 📈 Performance

- **Analysis Speed**: ~1000 lines of code per second
- **Memory Usage**: <100MB for typical projects
- **Output Size**: ~1-5MB documentation for medium projects
- **Build Time**: 30-60 seconds for full documentation generation

## 🔒 Security

- No external API calls during analysis
- Local processing only
- Configurable file inclusion/exclusion
- Safe AST parsing without code execution

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [MkDocs](https://www.mkdocs.org/) and [Material theme](https://squidfunk.github.io/mkdocs-material/)
- Code analysis powered by Python AST and [Radon](https://radon.readthedocs.io/)
- Diagrams created with [Diagrams](https://diagrams.mingrammer.com/) library
- Inspired by the need for always up-to-date documentation

## 📞 Support

- 📧 Create an issue for bug reports or feature requests
- 💬 Check existing issues for solutions
- 📖 Read the generated documentation for usage examples

---

**Auto-generated documentation for the win! 🎉**
