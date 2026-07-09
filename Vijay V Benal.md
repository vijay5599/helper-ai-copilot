Vijay V Benal
vijayvb5599@gmail.com | 6364534614 | linkedin.com/in/vijay-v-benal | github.com/vijay5599 | Portfolio
PROFESSIONAL SUMMARY
Full Stack Developer with 4 years of experience building scalable web applications and AI-driven
products using React.js, Next.js, FastAPI, Python, and Node.js. Hands-on experience integrating
LLMs, developing RESTful APIs, and deploying containerized applications with Docker on Azure and
Linux environments. Strong background in designing responsive user interfaces, optimizing
application performance, and delivering production-grade solutions across enterprise and internal
platforms. Passionate about building intelligent applications with modern web technologies and
cloud-native architectures.
SKILLS
Languages: JavaScript, Python, TypeScript, SQL, HTML, CSS
Frameworks & Libraries: React.js, Redux, FastAPI, Django, Node.js, Express.js , Next.js
Database & Cloud: PostgreSQL, MySQL, Chromadb, MongoDB
DevOps & Tools: Azure (Blob Storage, DevOps, App Services) , AWS (EC2, S3, IAM, CloudWatch,
ECS - Basic), Docker, GitLab CI/CD, VS Code, Git, Bash, Linux Shell Scripting
AI/LLM : RAG, Prompt Engineering, AI Chatbots, LLM Integration,
Langgraph, LangChain
EXPERIENCE
Software Engineer : Mindteck (Client : NetApp) August 2025 - Present
● Developed AI-powered features using Large Language Models (LLMs) to automate workflows and
improve user productivity.
● Built scalable full-stack applications using Next.js, React.js, FastAPI, and Python.
● Designed RAG-based AI solutions using embeddings and vector databases to deliver context-aware,
accurate responses.
● Developed and consumed RESTful APIs for seamless integration with enterprise systems.
● Optimized application performance through code profiling, caching, and API improvements, reducing
response times.
● Investigated and resolved production issues, improving application stability and reliability.
● Collaborated with cross-functional teams in Agile sprints to deliver enterprise-grade features for
NetApp products
Software Developer: Graphene AI August 2022 - August 2025
● Developed and maintained scalable web applications using React.js, Node.js, FastAPI, and
PostgreSQL.
● Built AI-powered content generation and automation tools by integrating OpenAI APIs and prompt
engineering techniques.
● Designed secure RESTful APIs with authentication, validation, and efficient database interactions.
● Developed responsive and reusable frontend components, improving application usability and
maintainability.
● Containerized applications with Docker and deployed services on Azure and Linux environments.
● Automated build and deployment pipelines using GitLab CI and Azure DevOps, enabling reliable
production releases.
● Worked closely with product managers, designers, and QA teams in Agile environments to deliver
high-quality software.
PROJECTS



ArticleAgent Interview Prep
Project Explanation
ArticleAgent is an AI-powered content automation platform I built to generate high-quality, SEO-friendly articles at scale. The main goal was to solve common problems with AI writing tools such as weak structure, factual errors, robotic tone, and poor long-form coherence.
On the frontend, I used React.js with Tailwind CSS and Material UI to build a responsive dashboard. Users can configure inputs like tone, industry, target word count, and humanization level. I also built a real-time editor so users can review and refine content easily.
On the backend, I used FastAPI for high-performance async APIs. I used PostgreSQL for storing users, projects, and generated content. Authentication is handled with JWT.
The core strength of the project is the multi-stage AI pipeline.
First, a Planner Agent creates a structured JSON outline for the article. This keeps long-form content organized and ensures all key topics are covered.
Next, a Research Agent gathers supporting information and context. This helps reduce hallucinations and improves factual grounding.
Then, section generation happens in parallel using Python asyncio. Each article section is generated independently, which reduces response time and allows large articles without context window issues.
After that, augmentation agents suggest charts, visuals, infographics, and images to improve engagement.
Finally, a Humanization and Validation layer rewrites the content to sound more natural and checks whether the output matches user instructions like tone, word count, and format.
For model orchestration, I used LiteLLM, which lets the system switch between providers like GPT-4o, Claude, and Gemini based on task needs, cost, or availability.
For monitoring, I integrated Langfuse to track prompts, token usage, latency, failures, and costs.
For deployment, I containerized the full stack using Docker and deployed it on a Linux VM. I also set up GitLab CI/CD pipelines for automated testing and deployment.
This project gave me hands-on experience in scalable backend systems, async processing, multi-model AI orchestration, prompt pipelines, DevOps, and building production-grade AI products.
Challenge Faced and How I Solved It
One challenge I faced while developing ArticleAgent was high article generation time, especially during peak usage hours. Users experienced delays, and sometimes requests timed out, which affected the overall experience.
My goal was to identify the bottlenecks and improve performance on both the backend and frontend so the platform could scale smoothly.

I started by profiling the backend and found that external AI API calls were being handled synchronously, which caused blocking during concurrent traffic. I refactored those services using FastAPI's async/await patterns and improved concurrency handling.

On the frontend, I optimized rendering by lazy loading heavy components like the editor, and used React.memo and useCallback to reduce unnecessary re-renders. I also added skeleton loaders and progress states to improve perceived performance.

As a result, article generation time improved by around 40%, responsiveness became much better under load, and users had a smoother experience.

LiteLLM — How to Explain It in an Interview
One-Line Answer
LiteLLM is a Python library that acts as a unified interface over multiple LLM providers — GPT-4o, Claude, Gemini — so your code does not need to change when you switch models.

Q: How do you know if the generated article is actually performing well for the user?

The ultimate test is user behavior. I look at the Acceptance Rate or Edit Distance in the real-time editor. If a user generates an article and publishes it with minimal tweaks, that's a success. If they are constantly rewriting entire sections, it means the generation pipeline needs tuning. Post-publishing, SEO metrics like organic traffic, time on page, and bounce rate are the final indicators.

ARG Project Interview Prep
Project Explanation
My second project was an AI-powered review automation platform called ARG, Automatic Review Generation.
The purpose of the tool was to automate code review and QA validation for test automation scripts. In many teams, engineers manually compare test scripts, qTest test steps, logs, and coding standards, which is time-consuming and error-prone. We built ARG to reduce manual effort and improve review quality.
The system analyzes automation test scripts, compares the script logic with qTest steps, and generates intelligent review comments automatically.
For example, it detects:
Missing test steps in the script
Mismatch between qTest steps and implemented code
Hardcoded values
Repetitive code that should be converted into reusable functions
Invalid docstring formats
Retry or connection handling issues
Test coverage gaps
Raw command usage needing best-practice improvements
On the frontend, I used Next.js to build a fast and responsive dashboard. It included review submission forms, review history, metrics dashboards, and action boards for users and managers.
On the backend, the system processed uploaded workspace paths, logs, and scripts, then ran validation pipelines using LLM APIs for intelligent code analysis and rule-based checks.
I also integrated review board publishing, where generated comments could be pushed directly into the internal review workflow.
The tool supported multiple review modes such as:
Code only review
Test steps vs code
Test steps vs code vs logs
It also tracked metrics like turnaround time, tool usage, and estimated AI cost.
This project helped improve engineering productivity by reducing manual review time and increasing consistency in QA validation.
Challenge Faced and How I Solved It
One major challenge in this project was handling large and inconsistent input data from multiple sources such as test scripts, qTest steps, and execution logs.
Different teams followed different formats, naming conventions, and documentation styles. Because of this, the AI model sometimes produced inaccurate comparisons or missed issues
My task was to improve reliability and make the review results consistent across projects.
I solved this by introducing a preprocessing layer before sending data to the LLM. I standardized script inputs, normalized qTest steps, cleaned logs, and converted all inputs into a structured format.
I also added rule-based validations before and after the AI analysis. This hybrid approach used deterministic checks for simple rules and LLM reasoning for complex comparisons.
In addition, I improved prompts and added retry/fallback handling for API failures.
As a result, review accuracy improved significantly, false positives were reduced, and users trusted the tool more for daily code reviews.
AI Role in the Project — How I Utilized It
AI was the core intelligence layer in ARG. Without it, the tool would have been a basic linter. With it, the tool became a context-aware reviewer that could reason about logic, intent, and test coverage — something rule-based systems alone cannot do.
What AI Was Used For
1. Intelligent Code Review and Comment Generation The primary use of AI was to analyze automation test scripts and generate contextual review comments. I sent structured prompts to an LLM API — containing the test script, the corresponding qTest steps, and execution logs — and the model returned review comments highlighting mismatches, missing coverage, and quality issues.
2. Script-to-Step Comparison One of the most complex tasks was comparing what was written in the test script versus what was described in the qTest test steps. This is not a simple string match — it requires understanding intent. I used the LLM to reason about whether the code logically implements the defined test steps, even when naming conventions or variable names differ.
3. Log Analysis and Failure Root Cause Identification When execution logs were included, I prompted the AI to correlate log output with the test script and qTest steps to help identify why a test might be failing — for example, detecting a missing assertion, an unhandled exception, or a retry not being implemented.
4. Docstring and Code Quality Review The model was also used to evaluate docstring quality, flag hardcoded values, identify repetitive logic that should be abstracted into reusable functions, and suggest improvements aligned with the team's coding standards.
AI Cost Tracking
I tracked token usage per review run — prompt tokens, completion tokens, and estimated cost. This was surfaced in the metrics dashboard so managers could monitor AI usage and control spending.
Impact
Replaced hours of manual code review with automated, AI-generated feedback in seconds
Reduced false positives through the hybrid validation approach
Improved review consistency across teams regardless of coding style differences
Gave engineers actionable, categorized feedback instead of generic warnings
Provided managers visibility into AI usage and estimated cost per review
Used a hybrid approach (AI + Rule-based) because static rules cannot verify if a test script logically implements semantic qTest steps, whereas LLMs can reason about intent."

