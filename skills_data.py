"""
skills_data.py
---------------
Curated, offline skill taxonomies used by the "Skill Gap" feature.

Each skill entry is a dict:
    {
        "name": str,               # canonical display name
        "priority": str,           # "core" | "important" | "nice-to-have"
        "tip": str,                # short, specific guidance shown when missing
        "aliases": [str, ...],     # optional alternate spellings/synonyms
                                    # checked in addition to `name` when
                                    # scanning the resume text
    }

"core"        -> resume readers / interviewers treat this as a baseline
                 expectation; missing it is a real red flag.
"important"   -> strongly expected, but its absence alone won't sink a
                 candidacy if the core skills are solid.
"nice-to-have"-> differentiators; good for standing out, not required.

This is deliberately a small, hand-picked list per role/tool rather than
an exhaustive one — the goal is a short, high-signal set of gaps to act
on, not an overwhelming checklist.
"""

ROLE_ICONS = {
    "Game Developer": "🎮",
    "Frontend Developer": "💻",
    "Backend Developer": "🖥️",
    "Data Scientist": "📊",
    "DevOps Engineer": "🔁",
    "Mobile Developer": "📱",
}

TOOL_ICONS = {
    "React": "⚛️",
    "Docker": "🐳",
    "Python": "🐍",
    "Kubernetes": "☸️",
    "AWS": "☁️",
    "Machine Learning": "🧠",
}

ROLE_SKILL_MAP = {
    "Game Developer": [
        {"name": "C++", "priority": "core",
         "tip": "Most game engines (Unreal, custom in-house engines) are built on C++ — strong fundamentals here matter a lot."},
        {"name": "Unity", "priority": "core",
         "tip": "Unity is the most in-demand engine for indie/mobile roles — ship at least one playable project in it."},
        {"name": "Unreal Engine", "priority": "important", "aliases": ["unreal"],
         "tip": "Unreal (Blueprints or C++) is the standard for AAA and 3D-heavy titles."},
        {"name": "Game Physics", "priority": "important", "aliases": ["collision detection", "rigidbody"],
         "tip": "Understand collision detection, rigidbody dynamics, and basic physics engines."},
        {"name": "3D Math", "priority": "important", "aliases": ["linear algebra", "vectors", "matrices", "quaternions"],
         "tip": "Vectors, matrices, and quaternions come up constantly in gameplay and camera code."},
        {"name": "Shader Programming", "priority": "nice-to-have", "aliases": ["hlsl", "glsl", "shaders"],
         "tip": "Basic HLSL/GLSL shader knowledge lets you own visual effects, not just gameplay code."},
        {"name": "Multiplayer Networking", "priority": "nice-to-have", "aliases": ["netcode"],
         "tip": "Client-server architecture and state sync are valuable if you're targeting online games."},
        {"name": "Version Control", "priority": "core", "aliases": ["git", "perforce"],
         "tip": "Git (or Perforce for large binary assets) is assumed baseline — make sure it's on your resume."},
    ],
    "Frontend Developer": [
        {"name": "React", "priority": "core",
         "tip": "Master hooks, component composition, and state management (Context or Redux/Zustand)."},
        {"name": "JavaScript", "priority": "core", "aliases": ["js", "es6"],
         "tip": "Deep JS fundamentals (closures, async/await, the event loop) are what interviews probe hardest."},
        {"name": "CSS", "priority": "core", "aliases": ["css3", "flexbox", "grid"],
         "tip": "Flexbox/Grid layout fluency and responsive design are non-negotiable for this role."},
        {"name": "TypeScript", "priority": "important",
         "tip": "Most modern frontend codebases are TypeScript-first — add it if you haven't."},
        {"name": "HTML", "priority": "core", "aliases": ["html5", "semantic html"],
         "tip": "Semantic HTML and accessibility basics (ARIA, alt text) matter for both UX and SEO."},
        {"name": "Testing", "priority": "important", "aliases": ["jest", "react testing library", "cypress", "playwright"],
         "tip": "Component testing (Jest + React Testing Library) or e2e (Cypress/Playwright) shows production maturity."},
        {"name": "Build Tools", "priority": "nice-to-have", "aliases": ["webpack", "vite", "bundler"],
         "tip": "Understanding build tooling (Vite/Webpack) helps you debug performance and bundle-size issues."},
        {"name": "Accessibility", "priority": "nice-to-have", "aliases": ["a11y", "wcag"],
         "tip": "WCAG-aware development is increasingly a hiring differentiator, not just a nice-to-have."},
    ],
    "Backend Developer": [
        {"name": "REST API", "priority": "core", "aliases": ["rest apis", "restful"],
         "tip": "Designing clean, versioned REST APIs is the baseline expectation."},
        {"name": "SQL", "priority": "core", "aliases": ["postgresql", "mysql", "databases"],
         "tip": "Comfort with relational schema design and query optimization is core to this role."},
        {"name": "System Design", "priority": "important",
         "tip": "Be ready to talk through scaling a service — caching, load balancing, database sharding."},
        {"name": "Docker", "priority": "important",
         "tip": "Containerizing a service end-to-end is now table stakes for backend roles."},
        {"name": "Authentication", "priority": "important", "aliases": ["oauth", "jwt"],
         "tip": "Know OAuth2/JWT-based auth flows, not just 'I used a library for login.'"},
        {"name": "Microservices", "priority": "nice-to-have",
         "tip": "Understanding service boundaries and inter-service communication is a plus at larger orgs."},
        {"name": "Message Queues", "priority": "nice-to-have", "aliases": ["kafka", "rabbitmq"],
         "tip": "Kafka/RabbitMQ experience signals you can handle async, high-throughput systems."},
        {"name": "Testing", "priority": "core", "aliases": ["unit testing", "integration testing"],
         "tip": "Unit + integration test coverage is one of the first things senior engineers check for."},
    ],
    "Data Scientist": [
        {"name": "Python", "priority": "core",
         "tip": "Python is the default language — make sure it's front and center, not buried."},
        {"name": "Pandas", "priority": "core",
         "tip": "Data wrangling with pandas is assumed daily-driver knowledge."},
        {"name": "Machine Learning", "priority": "core", "aliases": ["ml"],
         "tip": "Be ready to discuss model selection, evaluation metrics, and overfitting trade-offs."},
        {"name": "SQL", "priority": "important",
         "tip": "Most data scientists pull their own data — SQL fluency is expected."},
        {"name": "Statistics", "priority": "core", "aliases": ["hypothesis testing", "statistical analysis", "a/b testing"],
         "tip": "Hypothesis testing and experiment design (A/B testing) come up constantly in interviews."},
        {"name": "Data Visualization", "priority": "important", "aliases": ["matplotlib", "tableau", "power bi"],
         "tip": "Communicating findings visually (matplotlib/Tableau/Power BI) is as important as the modeling itself."},
        {"name": "Deep Learning", "priority": "nice-to-have", "aliases": ["tensorflow", "pytorch", "neural networks"],
         "tip": "TensorFlow/PyTorch exposure helps for roles touching NLP, vision, or recommendation systems."},
        {"name": "MLOps", "priority": "nice-to-have",
         "tip": "Knowing how models get deployed and monitored in production is a growing differentiator."},
    ],
    "DevOps Engineer": [
        {"name": "Docker", "priority": "core",
         "tip": "Containerization fundamentals (Dockerfiles, multi-stage builds) are the entry bar."},
        {"name": "Kubernetes", "priority": "core", "aliases": ["k8s"],
         "tip": "K8s orchestration (deployments, services, Helm charts) is the industry standard to know."},
        {"name": "CI/CD", "priority": "core", "aliases": ["continuous integration", "continuous deployment", "github actions", "jenkins"],
         "tip": "Hands-on CI/CD pipeline design (GitHub Actions, Jenkins, GitLab CI) is expected, not optional."},
        {"name": "AWS", "priority": "important", "aliases": ["azure", "gcp", "cloud"],
         "tip": "Deep knowledge of at least one major cloud provider (AWS/Azure/GCP) is usually required."},
        {"name": "Infrastructure as Code", "priority": "important", "aliases": ["terraform", "cloudformation"],
         "tip": "Terraform or CloudFormation experience shows you manage infra as code, not by hand."},
        {"name": "Linux", "priority": "core",
         "tip": "Comfortable shell scripting and Linux systems administration is foundational."},
        {"name": "Monitoring", "priority": "nice-to-have", "aliases": ["prometheus", "grafana", "datadog"],
         "tip": "Observability tooling (Prometheus/Grafana/Datadog) rounds out a strong DevOps profile."},
        {"name": "Networking", "priority": "nice-to-have", "aliases": ["dns", "vpc", "load balancer"],
         "tip": "Basic networking (DNS, load balancers, VPCs) helps you debug production issues faster."},
    ],
    "Mobile Developer": [
        {"name": "Swift", "priority": "important", "aliases": ["ios"],
         "tip": "Swift is the standard for native iOS — pair it with UIKit/SwiftUI experience."},
        {"name": "Kotlin", "priority": "important", "aliases": ["android"],
         "tip": "Kotlin is now the default for native Android over Java."},
        {"name": "React Native", "priority": "important", "aliases": ["flutter"],
         "tip": "Cross-platform experience (React Native or Flutter) broadens the roles you qualify for."},
        {"name": "Mobile UI Design", "priority": "core", "aliases": ["material design", "human interface guidelines"],
         "tip": "Platform-specific design guidelines (Material Design / HIG) show polish beyond 'it works.'"},
        {"name": "REST API", "priority": "core", "aliases": ["graphql"],
         "tip": "Consuming and caching REST/GraphQL APIs correctly is a daily skill for mobile roles."},
        {"name": "App Store Deployment", "priority": "nice-to-have", "aliases": ["fastlane", "play store", "app store"],
         "tip": "Shipping through App Store/Play Store review (ideally with CI like Fastlane) is a strong signal."},
        {"name": "Performance Optimization", "priority": "nice-to-have", "aliases": ["profiling"],
         "tip": "Battery/memory profiling experience separates mid from senior mobile engineers."},
    ],
}

TOOL_SKILL_MAP = {
    "React": [
        {"name": "JSX", "priority": "core",
         "tip": "Comfort reading/writing JSX and understanding how it compiles matters for debugging."},
        {"name": "Hooks", "priority": "core", "aliases": ["usestate", "useeffect"],
         "tip": "useState/useEffect/useMemo and custom hooks should be second nature."},
        {"name": "State Management", "priority": "core", "aliases": ["redux", "zustand", "context api"],
         "tip": "Know when to reach for Context vs Redux/Zustand for larger apps."},
        {"name": "React Router", "priority": "important",
         "tip": "Client-side routing patterns (nested routes, loaders) come up in most real apps."},
        {"name": "Component Testing", "priority": "important", "aliases": ["jest", "react testing library"],
         "tip": "Jest + React Testing Library is the standard combo for component-level tests."},
        {"name": "Performance Optimization", "priority": "nice-to-have", "aliases": ["memo", "usememo", "usecallback"],
         "tip": "React.memo/useMemo/useCallback knowledge shows you can debug re-render issues."},
    ],
    "Docker": [
        {"name": "Dockerfile", "priority": "core",
         "tip": "Writing efficient, minimal-layer Dockerfiles is the baseline skill."},
        {"name": "Docker Compose", "priority": "core",
         "tip": "Multi-container local dev setups via docker-compose are extremely common."},
        {"name": "Container Networking", "priority": "important",
         "tip": "Understand bridge networks, port mapping, and service discovery between containers."},
        {"name": "Image Optimization", "priority": "important", "aliases": ["multi-stage build"],
         "tip": "Multi-stage builds keep image size down — a common interview talking point."},
        {"name": "Volumes", "priority": "nice-to-have",
         "tip": "Persistent storage patterns (named volumes vs bind mounts) matter for stateful services."},
        {"name": "Container Security", "priority": "nice-to-have", "aliases": ["non-root user"],
         "tip": "Running containers as non-root and scanning images for vulnerabilities is a maturity signal."},
    ],
    "Python": [
        {"name": "Data Structures", "priority": "core",
         "tip": "Lists/dicts/sets fluency and knowing their time complexity is assumed baseline."},
        {"name": "OOP", "priority": "core", "aliases": ["object-oriented programming", "classes"],
         "tip": "Class design, inheritance vs composition, and dunder methods come up in interviews."},
        {"name": "Virtual Environments", "priority": "important", "aliases": ["venv", "poetry", "pipenv"],
         "tip": "Dependency isolation (venv/poetry) shows professional project hygiene."},
        {"name": "Testing", "priority": "important", "aliases": ["pytest", "unittest"],
         "tip": "pytest fluency (fixtures, parametrize, mocking) is expected for production code."},
        {"name": "Async Programming", "priority": "nice-to-have", "aliases": ["asyncio", "async/await"],
         "tip": "asyncio experience is increasingly relevant for I/O-heavy services."},
        {"name": "Packaging", "priority": "nice-to-have", "aliases": ["pip", "pyproject.toml"],
         "tip": "Knowing how to package and publish a library is a nice differentiator."},
    ],
    "Kubernetes": [
        {"name": "Pods & Deployments", "priority": "core", "aliases": ["pods", "deployments"],
         "tip": "Understand the pod lifecycle and how Deployments manage replica sets."},
        {"name": "Services", "priority": "core", "aliases": ["clusterip", "loadbalancer", "nodeport"],
         "tip": "Know the difference between ClusterIP, NodePort, and LoadBalancer service types."},
        {"name": "Helm", "priority": "important",
         "tip": "Helm charts are the standard way real teams package and deploy K8s apps."},
        {"name": "ConfigMaps & Secrets", "priority": "important", "aliases": ["configmap", "secrets"],
         "tip": "Externalizing config/secrets properly is a common interview and real-world requirement."},
        {"name": "Autoscaling", "priority": "nice-to-have", "aliases": ["hpa"],
         "tip": "Horizontal Pod Autoscaler experience shows you think about production load."},
        {"name": "Ingress", "priority": "nice-to-have",
         "tip": "Ingress controllers (nginx, traefik) for routing external traffic round out the picture."},
    ],
    "AWS": [
        {"name": "EC2", "priority": "core",
         "tip": "Core compute fundamentals — instance types, AMIs, security groups."},
        {"name": "S3", "priority": "core",
         "tip": "Object storage patterns, bucket policies, and lifecycle rules are widely used."},
        {"name": "IAM", "priority": "core", "aliases": ["identity and access management"],
         "tip": "IAM roles/policies are the backbone of AWS security — get comfortable with least privilege."},
        {"name": "Lambda", "priority": "important", "aliases": ["serverless"],
         "tip": "Serverless functions (Lambda) are common for event-driven architectures."},
        {"name": "VPC", "priority": "important", "aliases": ["networking"],
         "tip": "Subnetting, route tables, and security groups show cloud networking depth, not just services."},
        {"name": "Infrastructure as Code", "priority": "nice-to-have", "aliases": ["cloudformation", "terraform"],
         "tip": "Infra-as-code experience (CloudFormation/Terraform) is a strong plus for most cloud roles."},
    ],
    "Machine Learning": [
        {"name": "Supervised Learning", "priority": "core", "aliases": ["regression", "classification"],
         "tip": "Regression and classification fundamentals (and when to use which) are assumed."},
        {"name": "Model Evaluation", "priority": "core", "aliases": ["precision", "recall", "f1 score", "cross-validation"],
         "tip": "Know your metrics (precision/recall/F1/AUC) and how to avoid data leakage in validation."},
        {"name": "Feature Engineering", "priority": "important",
         "tip": "Good feature engineering often beats a fancier model — be ready to talk through examples."},
        {"name": "Scikit-learn", "priority": "important", "aliases": ["sklearn"],
         "tip": "scikit-learn is the default toolkit for classical ML — make sure it's explicitly named."},
        {"name": "Deep Learning", "priority": "nice-to-have", "aliases": ["neural networks", "tensorflow", "pytorch"],
         "tip": "Neural network basics (with TensorFlow or PyTorch) matter for NLP/vision-heavy roles."},
        {"name": "Model Deployment", "priority": "nice-to-have", "aliases": ["mlops", "model serving"],
         "tip": "Knowing how a model actually gets served in production is a growing expectation."},
    ],
}