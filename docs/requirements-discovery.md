# Requirements & Discovery

Makena's scope came from two places: student personas we mapped up front, and a discovery meeting with real MSU staff. Almost every design decision traces back to something here.

## Student personas

**Transfer students**
1. How do I know which of my credits will transfer?
2. What's the process for declaring a major?
3. How do I meet with an academic advisor?
4. What resources help me adjust to a new campus?
5. How do I register, and is there priority registration for transfers?

**Freshmen**
1. How do I register as a new student?
2. How do I get my student ID?
3. How do I set up a parking permit and where can I park?
4. How do I schedule an advising appointment?
5. What dining, housing, and campus resources are available?

**Seniors**
1. How do I apply for graduation and what are the deadlines?
2. How do I confirm I've met all degree requirements?
3. What career services are available?
4. How do I request transcripts or recommendation letters?
5. What happens to my accounts and access after I graduate?

## Functional requirements

1. Answer FAQs about campus services (library, gym, advising hours, parking, student ID).
2. Guide students through course registration, including new vs. transfer steps.
3. Explain credit-transfer policy and the process for declaring a major.
4. Provide graduation info — how to apply, deadlines, degree-requirement checklists.
5. Route to career services, transcript requests, and advisor contacts for anything it can't resolve.

## Persona & tone

**Name:** Makena (the first two letters of each teammate's first name — Ma/Ke/Na).
**Tone:** friendly, helpful, professional — approachable but clear.

**Ethical constraints (turned into hard prompt rules):**
- Never share a student's personal information; the only contacts shared are publicly listed advisor/office emails.
- Never ask for or accept logins, passwords, or sensitive details.
- Answer only from verified university sources; if unsure, route to an advisor instead of guessing.
- No political/religious/personal-belief discussion — redirect to academic support.
- No roleplay or persona-switching, regardless of how a request is framed.
- No help with academic dishonesty or AI-generated submissions.
- On a suspected mental-health crisis, skip advice and immediately give the counseling center's contact and location.

## Conversation design

A **happy path** (course registration: ask intent → collect course → confirm details → give portal steps → close) and a **fallback path** (complex prerequisites: check prerequisites → identify the student may not qualify → explain requirements → on an exception request, hand off to an advisor with contact info and a booking suggestion).

## Advisor discovery meeting — what changed the build

We met with academic advisors, a department director, and a tech lead before finalizing. Key feedback, all incorporated:

- **Prerequisites are the highest-priority use case.**
- The bot had given an incorrect retention GPA for Finance — corrected with the accurate 2.0 figure.
- The director wanted **Navigate appointment booking** — implemented by hardcoding the booking URL in the system prompt.
- **HR, employment, and Title IX** coverage was required — added to the knowledge base with direct routing rules.
- A **legal-liability concern** was raised — resolved with the AI disclaimer on every response.
- **Source links** required on all answers so students can verify independently.
- **Sexual-assault routing** corrected to go directly to the Title IX office, with a note that the process differs for commuter vs. residential students.
