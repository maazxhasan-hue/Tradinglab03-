# Nexora AI Agent Catalog

Generated from `company/roles.json` and the canonical growth roster in `company/nexora_growth_runtime.py`.

**Important:** registration is not proof of working execution. A role is considered verified only when acceptance tests pass and task evidence exists.

- Company role entries: 155
- Growth team roles: 41
- Total registry entries: 196

## Company workforce roles

### Executive & Strategy

- [ ] CEO / Strategy Lead
- [ ] Operations Orchestrator
- [ ] Project Manager
- [ ] Delivery Director
- [ ] Risk Committee Coordinator
- [ ] Harvey Agent
- [ ] Project Operations Agent
- [ ] Workflow Agent
- [ ] Knowledge & Memory Agent
- [ ] Chief of Staff Agent
- [ ] Decision Intelligence Agent
- [ ] Company Memory Curator
- [ ] Agent Performance Auditor

### Marketing & Brand

- [ ] Marketing Director
- [ ] Content Marketing Agent
- [ ] SEO Specialist
- [ ] Social Media Manager
- [ ] Brand Strategist
- [ ] Campaign Operator
- [ ] Marketing Analyst
- [ ] Marketing Agent
- [ ] Brand Agent
- [ ] Instagram Growth Agent
- [ ] Social & Community Agent
- [ ] Reverse Writing Agent
- [ ] Creative Brief Agent
- [ ] Brand Voice QA Agent
- [ ] Short-Form Video Planner
- [ ] Campaign Experiment Designer

### Sales & Partnerships

- [ ] Sales Director
- [ ] Lead Researcher
- [ ] Qualification Agent
- [ ] Proposal Writer
- [ ] Partnerships Manager
- [ ] Sales Operations Analyst
- [ ] Business Intelligence & Revenue Scout
- [ ] Sales Agent
- [ ] Lead Discovery Agent
- [ ] Contact Agent
- [ ] Account Research Agent
- [ ] Objection Handling Drafter
- [ ] Client Onboarding Agent
- [ ] Retention Strategy Agent

### Customer Success & CA

- [ ] Customer Success Lead
- [ ] Client Account Manager (CA)
- [ ] Client Onboarding Specialist
- [ ] Customer Support Agent
- [ ] Customer Education Writer
- [ ] Retention & Feedback Analyst
- [ ] Client Support Agent

### Product & Service Design

- [ ] Product Lead
- [ ] Service Designer
- [ ] Product Researcher
- [ ] Pricing Research Analyst
- [ ] User Researcher
- [ ] Product Manager Agent
- [ ] Pricing Agent
- [ ] Landing Page Agent

### Research & Analysis

- [ ] Research Director
- [ ] Market Research Analyst
- [ ] Competitive Intelligence Analyst
- [ ] Data Analyst
- [ ] Experiment Analyst
- [ ] Growth Analysis Agent
- [ ] Experiment & Learning Agent
- [ ] Policy & Compliance Agent

### Builders & Engineering

- [ ] Engineering Director
- [ ] Website Builder
- [ ] Frontend Developer
- [ ] Backend Developer
- [ ] Full-Stack Developer
- [ ] Automation Developer
- [ ] AI Agent Developer
- [ ] Integration Engineer
- [ ] DevOps Engineer
- [ ] Website Making Agent
- [ ] Release & Development Agent

### Creative & Presenting

- [ ] Creative Director
- [ ] Graphic Designer
- [ ] UX/UI Designer
- [ ] Video Editor
- [ ] Copywriter
- [ ] Presentation Designer
- [ ] Demo & Pitch Presenter
- [ ] Voice Producer
- [ ] Video Editing Agent
- [ ] Cinematic Video Production Agent

### Quality, Audit & Testing

- [ ] Quality Director
- [ ] QA Tester
- [ ] Code Reviewer
- [ ] Website Auditor
- [ ] Accessibility Auditor
- [ ] Security Reviewer
- [ ] Red-Team Tester
- [ ] Release Acceptance Tester
- [ ] Process Auditor
- [ ] Testing & QA Agent
- [ ] Security & Privacy Agent
- [ ] SEO Web Agent
- [ ] Trading System Agent

### Delivery & Project Management

- [ ] Project Scheduler
- [ ] Resource Planner
- [ ] Delivery Coordinator
- [ ] Documentation Specialist
- [ ] Change Manager
- [ ] Release Manager

### Finance, Legal & Procurement

- [ ] Finance Lead
- [ ] Bookkeeper
- [ ] Invoicing & Collections Analyst
- [ ] Cash-Flow Analyst
- [ ] Budget & Forecast Analyst
- [ ] Procurement Analyst
- [ ] Contract Review Coordinator
- [ ] Compliance Coordinator

### People & Agent Operations

- [ ] People Operations Lead
- [ ] Recruitment Agent
- [ ] Capability Testing Agent
- [ ] Training Coordinator
- [ ] Performance Evaluator
- [ ] Promotion & Bonus Reviewer
- [ ] Access Provisioning Coordinator

### IT, Security & Data

- [ ] Security Lead
- [ ] Identity & Access Administrator
- [ ] Secrets Manager
- [ ] Monitoring Analyst
- [ ] Incident Response Coordinator
- [ ] Backup & Recovery Operator
- [ ] Privacy & Retention Coordinator

### Partnerships & Ecosystem

- [ ] Referral Partnerships Manager
- [ ] Subcontractor Coordinator
- [ ] Vendor Manager
- [ ] Platform Relations Coordinator

### Continuous Improvement

- [ ] Operations Excellence Lead
- [ ] Retrospective Facilitator
- [ ] Process Improvement Analyst
- [ ] Automation Opportunity Analyst
- [ ] KPI Reviewer
- [ ] Customer Feedback Analyst

### Research & Intelligence

- [ ] Evidence Verification Agent
- [ ] Market Sizing Agent
- [ ] Industry Research Agent
- [ ] Source Citation Auditor

### Websites & Software

- [ ] Frontend Builder Agent
- [ ] Backend Builder Agent
- [ ] API Integration Agent
- [ ] Accessibility QA Agent
- [ ] Automated Test Engineer

### Operations & Delivery

- [ ] Task Decomposition Agent
- [ ] Dependency Tracking Agent
- [ ] Delivery Evidence Collector
- [ ] Incident Triage Agent

### Finance & Administration

- [ ] Pricing Analysis Agent
- [ ] Budget Control Agent
- [ ] Invoice Workflow Agent

### Security & Compliance

- [ ] Security Review Agent

## Growth team roles

- [ ] Growth Director
- [ ] Content Lead
- [ ] Content Strategist
- [ ] Script & Copywriter
- [ ] Video/Creative Producer
- [ ] Content QA & Repurposing Specialist
- [ ] Research Lead
- [ ] Market Trend Analyst
- [ ] Audience/ICP Researcher
- [ ] Competitor Intelligence Analyst
- [ ] Keyword & Topic Researcher
- [ ] Lead Intelligence Lead
- [ ] Inbound Intent Classifier
- [ ] Public Prospect Researcher
- [ ] Lead Enrichment & Source Tracker
- [ ] Lead Quality Reviewer
- [ ] Sales Conversion Lead
- [ ] Enquiry Qualifier
- [ ] Proposal & Scope Drafter
- [ ] Follow-up Planner
- [ ] Meeting & Calendar Coordinator
- [ ] Community Lead
- [ ] Comment & DM Triage Agent
- [ ] Customer Support Drafter
- [ ] Feedback & Review Analyst
- [ ] Response Escalation Specialist
- [ ] Distribution Lead
- [ ] Social Scheduling Coordinator
- [ ] SEO & Website Distribution Specialist
- [ ] Campaign Link & UTM Manager
- [ ] Campaign QA Specialist
- [ ] Growth Analytics Lead
- [ ] Content Performance Analyst
- [ ] Funnel & Attribution Analyst
- [ ] Experiment Planner
- [ ] Reporting Specialist
- [ ] Quality & Operations Lead
- [ ] Brand/Claims Reviewer
- [ ] Privacy, Consent & Platform Policy Reviewer
- [ ] Workflow Reliability & Audit Agent
- [ ] Compliance Audit Specialist

## End-to-end acceptance gate

1. Unique agent ID, correct department, and task creation.
2. Allowed task-state transitions; completion requires a non-empty output and evidence references.
3. Provider success returns non-empty output; provider failures become safe, actionable categories.
4. Role-specific deliverable contract is included in the execution prompt.
5. Local memory write succeeds; recall works where matching memories exist.
6. Restart recovery requeues interrupted work without retrying completed work.
7. Shared provider cooldown prevents immediate retry storms after HTTP 429.
8. External actions remain draft-only and approval-gated.
9. Live-provider smoke tests are run separately from mocked tests; no secrets or provider response bodies in logs.
