```mermaid
flowchart TD
    A[Scheduler<br/>cron / OpenClaw / Hermes] --> B[Job Fetcher Process]

    B --> C[GitHub Fetcher<br/>iCIMS / official GitHub Careers]
    B --> D[GitLab Fetcher<br/>Greenhouse]
    B --> E[Future Fetchers<br/>Lever / Workday / Ashby]

    C --> F[Normalize Job Data]
    D --> F
    E --> F

    F --> G[(SQLite Database)]

    G --> H[seen_jobs<br/>dedupe only]
    G --> I[collected_jobs<br/>raw job data + metadata]

    I --> J[Unanalyzed Job Selector]

    J --> K[Hermes / OpenClaw Analysis Agent]

    L[Candidate Profile<br/>resume + target roles + preferences] --> K

    K --> M[job_analysis<br/>score + strengths + gaps + recommendation]

    M --> N{Score Threshold Met?}

    N -- Yes --> O[Telegram Notifier]
    N -- No --> P[Store Only / No Alert]

    O --> Q[Phone Alert<br/>Apply / Watch / Skip Summary]