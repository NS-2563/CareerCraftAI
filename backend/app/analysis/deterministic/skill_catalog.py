"""Canonical skill catalog — comprehensive, categorized skill lists for deterministic skill analysis.

All lists are exhaustive but extensible. Each skill appears in exactly one primary category.
Supports normalization of variant forms to canonical names.
"""
from typing import Dict, List, Set, Tuple

# ---------------------------------------------------------------------------
# Canonical categorized skill lists
# ---------------------------------------------------------------------------

PROGRAMMING_LANGUAGES: Set[str] = {
    "python", "java", "javascript", "typescript", "go", "golang",
    "rust", "c++", "c", "c#", "csharp", "swift", "kotlin",
    "ruby", "php", "scala", "r", "dart", "perl", "haskell",
    "lua", "groovy", "elixir", "clojure", "erlang", "fortran",
    "cobol", "assembly", "vba", "matlab", "julia",
}

FRAMEWORKS: Set[str] = {
    "react", "angular", "vue", "vue.js", "svelte",
    "django", "flask", "fastapi", "spring", "spring boot",
    "express", "next.js", "nuxt", "rails", "laravel",
    "asp.net", ".net", "dotnet", "jquery",
    "bootstrap", "tailwind", "tailwind css", "sass", "scss",
    "redux", "vuex", "graphql", "apollo",
    "hibernate", "mybatis", "entity framework",
    "node.js", "nodejs", "deno", "bun",
    "electron", "react native", "flutter", "xamarin",
    "tensorflow", "pytorch", "keras", "scikit-learn",
    "pandas", "numpy", "matplotlib", "seaborn",
    "opencv", "nltk", "spacy", "hugging face",
    "junit", "jest", "mocha", "cypress", "selenium",
    "playwright", "pytest", "unittest",
    "qt", "wxwidgets", "winforms", "wpf",
    "ros", "opengl", "vulkan", "directx",
    "hadoop", "spark", "kafka", "flink",
}

DATABASES: Set[str] = {
    "sql", "mysql", "postgresql", "postgres", "sqlite",
    "mongodb", "mongo", "redis", "oracle", "oracle db",
    "sql server", "mssql", "mariadb",
    "cassandra", "dynamodb", "firebase", "supabase",
    "cockroachdb", "neo4j", "elasticsearch",
    "couchdb", "couchbase", "influxdb", "timescaledb",
    "memcached", "snowflake", "bigquery", "redshift",
    "databricks", "clickhouse", "duckdb",
    "prisma", "drizzle", "typeorm", "sequelize",
    "mongoose", "sqlalchemy",
}

CLOUD_TECHNOLOGIES: Set[str] = {
    "aws", "azure", "gcp", "google cloud", "amazon web services",
    "docker", "kubernetes", "k8s",
    "terraform", "pulumi", "ansible", "chef", "puppet",
    "jenkins", "github actions", "gitlab ci", "circleci",
    "ci/cd", "argocd", "helm",
    "heroku", "vercel", "netlify", "cloudflare",
    "istio", "envoy", "linkerd",
    "prometheus", "grafana", "datadog", "new relic",
    "splunk", "elk", "elastic stack", "loki",
    "serverless", "lambda", "cloud run", "ecs", "eks",
    "ec2", "s3", "rds", "vpc", "iam",
    "cloudfront", "route53", "api gateway",
}

TOOLS: Set[str] = {
    "git", "github", "gitlab", "bitbucket",
    "jira", "confluence", "slack", "teams",
    "vscode", "visual studio", "intellij", "pycharm",
    "eclipse", "vim", "neovim", "emacs",
    "postman", "swagger", "insomnia",
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "excel", "power bi", "tableau", "looker",
    "word", "powerpoint", "outlook",
    "notion", "obsidian", "roam",
    "nginx", "apache", "iis", "caddy",
    "webpack", "vite", "rollup", "esbuild", "parcel",
    "babel", "eslint", "prettier", "husky",
    "npm", "yarn", "pnpm", "pip", "conda", "maven", "gradle",
    "make", "cmake", "ninja",
    "gdb", "lldb", "valgrind", "perf",
    "wireshark", "burp suite", "nmap", "metasploit",
    "virtualbox", "vmware", "vagrant",
    "latex", "markdown", "yaml", "json", "xml",
}

TECHNOLOGIES: Set[str] = {
    "rest", "rest api", "restful", "graphql", "grpc",
    "microservices", "soa", "event-driven", "cqrs",
    "oauth", "oauth2", "jwt", "saml", "openid connect",
    "ssl", "tls", "https", "mfa",
    "websocket", "sse", "webhook",
    "api", "api design", "api gateway",
    "agile", "scrum", "kanban", "lean",
    "tdd", "bdd", "ci/cd", "devops", "devsecops",
    "docker", "containerization", "orchestration",
    "monolith", "distributed systems", "high availability",
    "load balancing", "caching", "cdn",
    "testing", "unit testing", "integration testing", "e2e",
    "ioc", "dependency injection", "aop",
    "mvc", "mvvm", "mvp", "clean architecture",
    "solid", "design patterns", "domain driven design",
    "functional programming", "oop", "reactive programming",
    "machine learning", "deep learning", "nlp", "computer vision",
    "llm", "rag", "fine-tuning", "prompt engineering",
    "data engineering", "etl", "data pipeline", "data warehouse",
    "data analysis", "statistics", "a/b testing",
    "security", "cybersecurity", "penetration testing",
    "networking", "tcp/ip", "dns", "http",
    "linux", "unix", "bash", "shell", "powershell",
    "windows server", "active directory", "ldap",
    "monitoring", "observability", "telemetry",
    "logging", "tracing", "alerting",
    "performance optimization", "profiling",
    "localization", "internationalization", "accessibility",
    "seo", "analytics", "a/b testing",
    "redis", "rabbitmq", "nats",
}

SOFT_SKILLS: Set[str] = {
    "leadership", "team leadership", "technical leadership",
    "communication", "written communication", "verbal communication",
    "teamwork", "collaboration", "cross-functional collaboration",
    "problem solving", "critical thinking", "analytical thinking",
    "mentoring", "coaching", "training",
    "adaptability", "flexibility", "resilience",
    "time management", "prioritization", "organization",
    "project management", "program management", "product management",
    "conflict resolution", "negotiation", "mediation",
    "creativity", "innovation", "strategic thinking",
    "decision making", "judgment",
    "emotional intelligence", "empathy",
    "public speaking", "presentation", "storytelling",
    "customer focus", "client management", "stakeholder management",
    "self-motivation", "initiative", "ownership",
    "attention to detail", "thoroughness",
    "research", "investigation",
    "reporting", "documentation", "technical writing",
    "interpersonal skills", "relationship building",
    "change management", "continuous improvement",
    "delegation", "resource management", "budgeting",
}

# ---------------------------------------------------------------------------
# Normalization map: variant → canonical name
# ---------------------------------------------------------------------------
# Only map true synonyms. Do NOT merge unrelated skills.
# Key = lowercase variant, Value = canonical display name.

_NORMALIZATION_MAP: Dict[str, str] = {
    # Programming language variants
    "js": "JavaScript",
    "ts": "TypeScript",
    "c#": "C#",
    "csharp": "C#",
    "c plus plus": "C++",
    "golang": "Go",
    # Framework / runtime variants
    "reactjs": "React",
    "react.js": "React",
    "vuejs": "Vue.js",
    "vue": "Vue.js",
    "nodejs": "Node.js",
    "node": "Node.js",
    "next": "Next.js",
    "nextjs": "Next.js",
    "nuxtjs": "Nuxt",
    "expressjs": "Express",
    "express.js": "Express",
    "dotnet": ".NET",
    "dot net": ".NET",
    "tailwindcss": "Tailwind CSS",
    "tailwind": "Tailwind CSS",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "huggingface": "Hugging Face",
    # Database variants
    "postgres": "PostgreSQL",
    "mongo": "MongoDB",
    "mssql": "SQL Server",
    "sql server": "SQL Server",
    "oracle db": "Oracle",
    # Cloud variants
    "k8s": "Kubernetes",
    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "amazon web services": "AWS",
    "aws lambda": "Lambda",
    "ci/cd": "CI/CD",
    "github actions": "GitHub Actions",
    "gitlab ci/cd": "GitLab CI",
    # Tool variants
    "vscode": "VS Code",
    "visual studio code": "VS Code",
    "intellij idea": "IntelliJ IDEA",
    "powerbi": "Power BI",
    # Technology variants
    "restful": "REST",
    "rest api": "REST",
    "oauth2": "OAuth 2.0",
    "oauth": "OAuth 2.0",
    "ssl/tls": "TLS",
    "e2e": "End-to-End Testing",
    "solid principles": "SOLID",
}

# ---------------------------------------------------------------------------
# Category labels for output
# ---------------------------------------------------------------------------

CATEGORY_LABELS: Dict[str, str] = {
    "programming_languages": "Programming Languages",
    "frameworks": "Frameworks",
    "databases": "Databases",
    "cloud_technologies": "Cloud Technologies",
    "tools": "Tools",
    "technologies": "Technologies",
    "soft_skills": "Soft Skills",
}

# ---------------------------------------------------------------------------
# Reverse lookup: category → set of canonical (lowercase) skill names
# ---------------------------------------------------------------------------

def _build_category_index() -> Dict[str, Set[str]]:
    return {
        "programming_languages": {s.lower() for s in PROGRAMMING_LANGUAGES},
        "frameworks": {s.lower() for s in FRAMEWORKS},
        "databases": {s.lower() for s in DATABASES},
        "cloud_technologies": {s.lower() for s in CLOUD_TECHNOLOGIES},
        "tools": {s.lower() for s in TOOLS},
        "technologies": {s.lower() for s in TECHNOLOGIES},
        "soft_skills": {s.lower() for s in SOFT_SKILLS},
    }


CATEGORY_INDEX: Dict[str, Set[str]] = _build_category_index()

# ---------------------------------------------------------------------------
# All canonical skills (lowercase) for fast lookup
# ---------------------------------------------------------------------------

_ALL_CANONICAL: Set[str] = set()
for _cat_set in CATEGORY_INDEX.values():
    _ALL_CANONICAL.update(_cat_set)

# ---------------------------------------------------------------------------
# Certification → skill inference mapping
# Maps certification name patterns to (skill_name, category)
# ---------------------------------------------------------------------------

CERTIFICATION_SKILL_MAP: Dict[str, Tuple[str, str]] = {
    # AWS
    "aws certified solutions architect": ("AWS", "cloud_technologies"),
    "aws certified developer": ("AWS", "cloud_technologies"),
    "aws certified sysops": ("AWS", "cloud_technologies"),
    "aws certified devops": ("AWS", "cloud_technologies"),
    "aws certified security": ("AWS", "cloud_technologies"),
    "aws certified data analytics": ("AWS", "cloud_technologies"),
    "aws certified machine learning": ("AWS", "cloud_technologies"),
    "aws certified database": ("AWS", "cloud_technologies"),
    # Azure
    "azure administrator": ("Azure", "cloud_technologies"),
    "azure developer": ("Azure", "cloud_technologies"),
    "azure solutions architect": ("Azure", "cloud_technologies"),
    "azure devops engineer": ("Azure", "cloud_technologies"),
    "azure security engineer": ("Azure", "cloud_technologies"),
    "azure data scientist": ("Azure", "cloud_technologies"),
    "azure ai engineer": ("Azure", "cloud_technologies"),
    # Google Cloud
    "google cloud associate": ("Google Cloud", "cloud_technologies"),
    "google cloud professional": ("Google Cloud", "cloud_technologies"),
    "google cloud data engineer": ("Google Cloud", "cloud_technologies"),
    "google cloud developer": ("Google Cloud", "cloud_technologies"),
    "google cloud architect": ("Google Cloud", "cloud_technologies"),
    # Kubernetes
    "certified kubernetes administrator": ("Kubernetes", "cloud_technologies"),
    "certified kubernetes developer": ("Kubernetes", "cloud_technologies"),
    "certified kubernetes security": ("Kubernetes", "cloud_technologies"),
    # Docker
    "docker certified": ("Docker", "cloud_technologies"),
    # Terraform
    "terraform associate": ("Terraform", "cloud_technologies"),
    "terraform professional": ("Terraform", "cloud_technologies"),
    # Security
    "cissp": ("Cybersecurity", "technologies"),
    "cisa": ("Cybersecurity", "technologies"),
    "cism": ("Cybersecurity", "technologies"),
    "ceh": ("Cybersecurity", "technologies"),
    "oscp": ("Cybersecurity", "technologies"),
    "comptia security+": ("Cybersecurity", "technologies"),
    "comptia network+": ("Networking", "technologies"),
    # Project Management
    "pmp": ("Project Management", "soft_skills"),
    "certified scrummaster": ("Agile", "technologies"),
    "certified scrum master": ("Agile", "technologies"),
    "csm": ("Agile", "technologies"),
    "safe agilist": ("Agile", "technologies"),
    "prince2": ("Project Management", "soft_skills"),
    # Data
    "certified data analyst": ("Data Analysis", "technologies"),
    "certified data scientist": ("Machine Learning", "technologies"),
    # Programming
    "oracle certified java": ("Java", "programming_languages"),
    "oracle java certified": ("Java", "programming_languages"),
    "microsoft certified": (".NET", "frameworks"),
    "python institute": ("Python", "programming_languages"),
    "pcep": ("Python", "programming_languages"),
    "pcap": ("Python", "programming_languages"),
    # Database
    "oracle database certification": ("Oracle", "databases"),
    "microsoft sql server certification": ("SQL Server", "databases"),
    "mongodb certified": ("MongoDB", "databases"),
    "mysql certified": ("MySQL", "databases"),
    # AI / ML
    "tensorflow developer": ("TensorFlow", "frameworks"),
    "tensorflow certification": ("TensorFlow", "frameworks"),
    "aws certified machine learning": ("Machine Learning", "technologies"),
    "google data engineering": ("Data Engineering", "technologies"),
}


def find_category(skill_name: str) -> str:
    """Return the category key for a canonical skill name, or 'uncategorized' if unknown."""
    lowered = skill_name.lower().strip()
    for cat, cat_set in CATEGORY_INDEX.items():
        if lowered in cat_set:
            return cat
    return "uncategorized"


_DISPLAY_NAMES: Dict[str, str] = {
    # Programming languages
    "python": "Python", "java": "Java", "javascript": "JavaScript",
    "typescript": "TypeScript", "go": "Go", "golang": "Go",
    "rust": "Rust", "c++": "C++", "c": "C", "c#": "C#", "csharp": "C#",
    "swift": "Swift", "kotlin": "Kotlin", "ruby": "Ruby", "php": "PHP",
    "scala": "Scala", "r": "R", "dart": "Dart", "perl": "Perl",
    "haskell": "Haskell", "lua": "Lua", "groovy": "Groovy",
    "elixir": "Elixir", "clojure": "Clojure", "erlang": "Erlang",
    "fortran": "Fortran", "cobol": "COBOL", "vba": "VBA",
    "assembly": "Assembly", "matlab": "MATLAB", "julia": "Julia",
    # Frameworks
    "react": "React", "angular": "Angular", "vue.js": "Vue.js",
    "svelte": "Svelte", "django": "Django", "flask": "Flask",
    "fastapi": "FastAPI", "spring": "Spring", "spring boot": "Spring Boot",
    "express": "Express", "next.js": "Next.js", "nuxt": "Nuxt",
    "rails": "Rails", "laravel": "Laravel", "asp.net": "ASP.NET",
    ".net": ".NET", "dotnet": ".NET",
    "jquery": "jQuery", "bootstrap": "Bootstrap",
    "tailwind css": "Tailwind CSS", "sass": "Sass", "scss": "SCSS",
    "redux": "Redux", "vuex": "Vuex", "graphql": "GraphQL",
    "apollo": "Apollo", "hibernate": "Hibernate", "mybatis": "MyBatis",
    "entity framework": "Entity Framework",
    "node.js": "Node.js", "deno": "Deno", "bun": "Bun",
    "electron": "Electron", "react native": "React Native",
    "flutter": "Flutter", "xamarin": "Xamarin",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch",
    "keras": "Keras", "scikit-learn": "scikit-learn",
    "pandas": "pandas", "numpy": "NumPy", "matplotlib": "Matplotlib",
    "seaborn": "Seaborn", "opencv": "OpenCV", "nltk": "NLTK",
    "spacy": "spaCy", "hugging face": "Hugging Face",
    "junit": "JUnit", "jest": "Jest", "mocha": "Mocha",
    "cypress": "Cypress", "selenium": "Selenium",
    "playwright": "Playwright", "pytest": "pytest",
    "qt": "Qt", "opengl": "OpenGL", "vulkan": "Vulkan",
    "directx": "DirectX", "ros": "ROS",
    "hadoop": "Hadoop", "spark": "Spark", "kafka": "Kafka",
    "flink": "Flink",
    # Databases
    "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL",
    "sqlite": "SQLite", "mongodb": "MongoDB", "mariadb": "MariaDB",
    "redis": "Redis", "oracle": "Oracle", "sql server": "SQL Server",
    "cassandra": "Cassandra", "dynamodb": "DynamoDB",
    "firebase": "Firebase", "supabase": "Supabase",
    "cockroachdb": "CockroachDB", "neo4j": "Neo4j",
    "elasticsearch": "Elasticsearch", "couchdb": "CouchDB",
    "couchbase": "Couchbase", "influxdb": "InfluxDB",
    "timescaledb": "TimescaleDB", "memcached": "Memcached",
    "snowflake": "Snowflake", "bigquery": "BigQuery",
    "redshift": "Redshift", "databricks": "Databricks",
    "clickhouse": "ClickHouse", "duckdb": "DuckDB",
    "prisma": "Prisma", "drizzle": "Drizzle", "typeorm": "TypeORM",
    "sequelize": "Sequelize", "mongoose": "Mongoose",
    "sqlalchemy": "SQLAlchemy",
    # Cloud
    "aws": "AWS", "azure": "Azure", "gcp": "GCP",
    "google cloud": "Google Cloud", "amazon web services": "AWS",
    "docker": "Docker", "kubernetes": "Kubernetes",
    "terraform": "Terraform", "pulumi": "Pulumi",
    "ansible": "Ansible", "chef": "Chef", "puppet": "Puppet",
    "jenkins": "Jenkins", "github actions": "GitHub Actions",
    "gitlab ci": "GitLab CI", "circleci": "CircleCI",
    "ci/cd": "CI/CD", "argocd": "ArgoCD", "helm": "Helm",
    "heroku": "Heroku", "vercel": "Vercel", "netlify": "Netlify",
    "cloudflare": "Cloudflare", "istio": "Istio", "envoy": "Envoy",
    "linkerd": "Linkerd", "prometheus": "Prometheus",
    "grafana": "Grafana", "datadog": "Datadog",
    "new relic": "New Relic", "splunk": "Splunk",
    "elk": "ELK", "elastic stack": "Elastic Stack",
    "loki": "Loki",
    "serverless": "Serverless", "lambda": "Lambda",
    "cloud run": "Cloud Run", "ecs": "ECS", "eks": "EKS",
    "ec2": "EC2", "s3": "S3", "rds": "RDS", "vpc": "VPC",
    "iam": "IAM", "cloudfront": "CloudFront",
    "route53": "Route 53", "api gateway": "API Gateway",
    # Tools
    "git": "Git", "github": "GitHub", "gitlab": "GitLab",
    "bitbucket": "Bitbucket", "jira": "Jira",
    "confluence": "Confluence", "slack": "Slack",
    "teams": "Teams", "vscode": "VS Code",
    "visual studio": "Visual Studio",
    "intellij": "IntelliJ", "pycharm": "PyCharm",
    "eclipse": "Eclipse", "vim": "Vim", "neovim": "Neovim",
    "emacs": "Emacs",
    "postman": "Postman", "swagger": "Swagger",
    "insomnia": "Insomnia", "figma": "Figma",
    "sketch": "Sketch", "adobe xd": "Adobe XD",
    "photoshop": "Photoshop", "illustrator": "Illustrator",
    "excel": "Excel", "power bi": "Power BI",
    "tableau": "Tableau", "looker": "Looker",
    "word": "Word", "powerpoint": "PowerPoint",
    "notion": "Notion", "obsidian": "Obsidian",
    "nginx": "Nginx", "apache": "Apache", "iis": "IIS",
    "caddy": "Caddy",
    "webpack": "Webpack", "vite": "Vite", "rollup": "Rollup",
    "esbuild": "esbuild", "parcel": "Parcel",
    "babel": "Babel", "eslint": "ESLint", "prettier": "Prettier",
    "husky": "Husky", "npm": "npm", "yarn": "Yarn",
    "pnpm": "pnpm", "pip": "pip", "conda": "Conda",
    "maven": "Maven", "gradle": "Gradle", "make": "Make",
    "cmake": "CMake", "ninja": "Ninja",
    "gdb": "GDB", "lldb": "LLDB", "valgrind": "Valgrind",
    "power bi": "Power BI",
    "wireshark": "Wireshark", "burp suite": "Burp Suite",
    "nmap": "Nmap", "metasploit": "Metasploit",
    "virtualbox": "VirtualBox", "vmware": "VMware",
    "vagrant": "Vagrant", "latex": "LaTeX",
    # Technologies
    "rest": "REST", "grpc": "gRPC",
    "oauth 2.0": "OAuth 2.0",
    "ssl": "SSL", "tls": "TLS",
    "websocket": "WebSocket",
    "agile": "Agile", "scrum": "Scrum", "kanban": "Kanban",
    "tdd": "TDD", "bdd": "BDD",
    "devops": "DevOps", "devsecops": "DevSecOps",
    "solid": "SOLID",
    "mvc": "MVC", "mvvm": "MVVM",
    "nlp": "NLP", "llm": "LLM", "rag": "RAG",
    "etl": "ETL",
    "linux": "Linux", "unix": "Unix",
    "bash": "Bash", "powershell": "PowerShell",
    "seo": "SEO",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "computer vision": "Computer Vision",
    "data engineering": "Data Engineering",
    "data analysis": "Data Analysis",
    "project management": "Project Management",
    "cybersecurity": "Cybersecurity",
    "networking": "Networking",
    "data science": "Data Science",
    # Soft skills
    "leadership": "Leadership",
    "communication": "Communication",
    "teamwork": "Teamwork",
    "problem solving": "Problem Solving",
    "critical thinking": "Critical Thinking",
    "time management": "Time Management",
    "mentoring": "Mentoring",
    "adaptability": "Adaptability",
}


def canonical_display_name(name: str) -> str:
    """Return the conventional display name for a skill.
    
    Handles case normalization (PYTHON → Python, DOCKER → Docker).
    Falls back to name if not in the display name map.
    """
    lowered = name.lower().strip()
    if lowered in _DISPLAY_NAMES:
        return _DISPLAY_NAMES[lowered]
    return name


def is_known_skill(name: str) -> bool:
    """Check if a name (after normalization) is in the canonical catalog."""
    return name.lower().strip() in _ALL_CANONICAL


def normalize_name(name: str) -> Tuple[str, bool]:
    """Normalize a skill name to its canonical form.
    
    Returns (canonical_name, was_normalized).
    """
    lowered = name.lower().strip()
    if lowered in _NORMALIZATION_MAP:
        return _NORMALIZATION_MAP[lowered], True
    return name, False


def get_certification_skills(cert_name: str) -> List[Tuple[str, str]]:
    """Derive skills from a certification name.
    
    Returns list of (skill_name, category) tuples.
    """
    lowered = cert_name.lower().strip()
    if lowered in CERTIFICATION_SKILL_MAP:
        return [CERTIFICATION_SKILL_MAP[lowered]]

    results = []
    for pattern, (skill, category) in CERTIFICATION_SKILL_MAP.items():
        if pattern in lowered:
            results.append((skill, category))
    return results
