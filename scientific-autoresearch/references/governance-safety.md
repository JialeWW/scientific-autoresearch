# Governance and Safety Gate

Read this file when work involves sensitive data, regulated research, physical actions, external systems, substantial compute or cost, or unclear authorization.

## 1. Classify the Work

Choose one or more classes:

- local computation over ordinary existing data;
- secondary analysis of confidential, personal, health, genomic, location, or otherwise sensitive data;
- external data acquisition or access-controlled resources;
- paid, shared, cluster, or high-impact computation;
- prospective human-participant, animal, clinical, field, or wet-lab research;
- hazardous, dual-use, environmental-release, device-control, or other safety-sensitive work;
- external communication, publication, submission, deployment, or modification of shared systems.

## 2. Build an Authorization Record

Before execution, record:

- who authorized the data, tools, compute, actions, and outputs;
- the protocol, approval, data-use agreement, consent, license, or policy that applies;
- permitted purpose, fields, populations, retention period, destinations, and sharing limits;
- the competent human responsible for live, regulated, hazardous, or clinical decisions;
- escalation, incident, adverse-event, and emergency stop procedures when applicable.

Do not infer approval from file access, tool availability, or a prior successful action.

## 3. Protect Data and Artifacts

- Keep raw data read-only and outside public output trees.
- Use the minimum necessary variables and rows.
- Remove direct identifiers and unnecessary quasi-identifiers before analysis artifacts are created.
- Store linkage keys separately under the data custodian's control.
- Prefer aggregate diagnostics; suppress small or identifying groups when required.
- Do not place secrets, access tokens, credentials, signed links, private endpoints, or restricted paths in commands, logs, inventories, or reports.
- Record hashes only when allowed; a hash does not make sensitive data public-safe.
- Honor deletion, retention, encryption, access-control, and locality requirements.

If safe data handling cannot be established, set `governance_status=blocked` and stop.

## 4. Bound External and Costly Actions

Require explicit approval before:

- downloading or purchasing new data;
- submitting paid, cluster, cloud, or materially costly jobs;
- contacting people or organizations;
- publishing, uploading, submitting, deploying, or changing shared systems;
- operating instruments, devices, robots, lab equipment, or field systems;
- creating or altering live experimental materials or procedures.

Before requesting approval, provide the exact proposed action, target, expected duration or cost, scientific purpose, failure modes, rollback or stop mechanism, and outputs.

## 5. Regulated and Physical Research

An agent may help design a protocol or analyze properly authorized records, but must not independently execute or expand live human, animal, clinical, field, wet-lab, hazardous, or dual-use work.

For such work:

- verify the approved protocol and responsible human before action;
- stay within the approved population, procedure, dose, material, endpoint, and stopping rules;
- do not convert an exploratory result into a protocol change without review and authorization;
- do not make clinical, participant-safety, animal-welfare, biosafety, or environmental-release decisions autonomously;
- stop on an adverse event, protocol deviation, safety signal, containment failure, or missing supervision according to the governing procedure.

## 6. Report the Gate

Record:

```text
governance_status
work_class
authorized_actions
prohibited_actions
data_controls
required_oversight
resource_limits
approval_references
stop_conditions
```

If the gate blocks execution, a design-only report may state what is missing and how an authorized human can proceed. Do not work around the gate.
