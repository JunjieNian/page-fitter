# page-fitter report

> **Triage mode** — semantic cost is type-class median, not per-candidate. Re-run without `--triage` for a higher-confidence ranking before applying multi-edit batches.

Current: **3 pages** — limit: **2** — need to lose: **1 page(s)**.

## High-leverage edits (4)
| ID | File:Line | Type | Δ lines | Leverage | Cost | Conf | Rationale |
|----|-----------|------|---------|----------|------|------|-----------|
| c092 | min.tex:103 | discourse_transition | -1.0 | 3.80 | 1 | medium | on last page; last-line fill 72%; next block is a paragraph (pullable) |
| c095 | min.tex:103 | sentence_descriptive | -1.0 | 3.80 | 2 | medium | on last page; last-line fill 72%; next block is a paragraph (pullable) |
| c113 | min.tex:113 | section_opening | -1.0 | 3.80 | 3 | medium | on last page; last-line fill 76%; next block is a paragraph (pullable) |
| c033 | min.tex:41 | sentence_descriptive | -1.0 | 0.10 | 2 | medium | last-line fill 100% |

## Marginal edits (2)
| ID | File:Line | Type | Δ lines | Leverage | Cost | Conf | Rationale |
|----|-----------|------|---------|----------|------|------|-----------|
| c034 | min.tex:42 | section_opening | -1.0 | 0.10 | 3 | medium | last-line fill 100% |
| c032 | min.tex:40 | sentence_claim | -1.0 | 0.10 | 4 | medium | last-line fill 100% |

## Not worth editing (112)
| ID | File:Line | Type | Δ lines | Leverage | Cost | Conf | Rationale |
|----|-----------|------|---------|----------|------|------|-----------|
| c001 | min.tex:1 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c002 | min.tex:1 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c003 | min.tex:2 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c004 | min.tex:2 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c005 | min.tex:3 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c006 | min.tex:4 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c007 | min.tex:5 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c008 | min.tex:7 | sentence_claim | +0.0 | 1.00 | 4 | low | last-line fill 0% |
| c009 | min.tex:8 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c010 | min.tex:20 | sentence_descriptive | +0.0 | 1.80 | 2 | medium | last-line fill 34%; next block is a paragraph (pullable) |
| c011 | min.tex:22 | discourse_transition | +0.0 | 1.80 | 1 | medium | last-line fill 34%; next block is a paragraph (pullable) |
| c012 | min.tex:26 | discourse_transition | +0.0 | 1.00 | 1 | low | last-line fill 0% |
| c013 | min.tex:23 | discourse_transition | +0.0 | 1.00 | 1 | low | last-line fill 0% |
| c014 | min.tex:28 | discourse_transition | +0.0 | 1.00 | 1 | low | last-line fill 0% |
| c015 | min.tex:28 | discourse_transition | +0.0 | 1.00 | 1 | low | last-line fill 0% |
| c016 | min.tex:20 | sentence_claim | +0.0 | 1.80 | 4 | low | last-line fill 34%; next block is a paragraph (pullable) |
| c017 | min.tex:22 | sentence_claim | +0.0 | 1.80 | 4 | low | last-line fill 34%; next block is a paragraph (pullable) |
| c018 | min.tex:23 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c019 | min.tex:26 | sentence_claim | +0.0 | 1.00 | 4 | low | last-line fill 0% |
| c020 | min.tex:28 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c021 | min.tex:28 | sentence_claim | +0.0 | 1.00 | 4 | low | last-line fill 0% |
| c022 | min.tex:33 | discourse_transition | +0.0 | -0.50 | 1 | medium | last-line fill 40% |
| c023 | min.tex:34 | discourse_transition | +0.0 | 1.00 | 1 | low | last-line fill 0% |
| c024 | min.tex:35 | discourse_transition | +0.0 | 1.80 | 1 | medium | last-line fill 38%; next block is a paragraph (pullable) |
| c025 | min.tex:34 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c026 | min.tex:35 | sentence_descriptive | +0.0 | 1.80 | 2 | low | last-line fill 38%; next block is a paragraph (pullable) |
| c027 | min.tex:37 | sentence_descriptive | +0.0 | 1.80 | 2 | medium | last-line fill 38%; next block is a paragraph (pullable) |
| c028 | min.tex:38 | discourse_transition | +0.0 | 1.80 | 1 | medium | last-line fill 38%; next block is a paragraph (pullable) |
| c029 | min.tex:39 | discourse_transition | +0.0 | 1.80 | 1 | medium | last-line fill 38%; next block is a paragraph (pullable) |
| c030 | min.tex:41 | discourse_transition | +0.0 | 0.10 | 1 | low | last-line fill 100% |
| c031 | min.tex:39 | sentence_descriptive | +0.0 | 1.80 | 2 | low | last-line fill 38%; next block is a paragraph (pullable) |
| c035 | min.tex:47 | discourse_transition | +0.0 | -0.50 | 1 | medium | last-line fill 6% |
| c036 | min.tex:46 | discourse_transition | +0.0 | -0.50 | 1 | medium | last-line fill 6% |
| c037 | min.tex:45 | discourse_transition | +0.0 | 1.00 | 1 | low | last-line fill 0% |
| c038 | min.tex:46 | sentence_descriptive | +0.0 | -0.50 | 2 | medium | last-line fill 6% |
| c039 | min.tex:47 | sentence_descriptive | +0.0 | -0.50 | 2 | medium | last-line fill 6% |
| c040 | min.tex:50 | sentence_descriptive | +0.0 | 2.40 | 2 | medium | last-line fill 2%; next block is a paragraph (pullable) |
| c041 | min.tex:50 | sentence_descriptive | +0.0 | 2.40 | 2 | medium | last-line fill 2%; next block is a paragraph (pullable) |
| c042 | min.tex:55 | discourse_transition | +0.0 | -0.50 | 1 | low | last-line fill 100% |
| c043 | min.tex:53 | discourse_transition | +0.0 | 1.80 | 1 | medium | last-line fill 17%; next block is a paragraph (pullable) |
| c044 | min.tex:54 | discourse_transition | +0.0 | -0.50 | 1 | low | last-line fill 100% |
| c045 | min.tex:56 | discourse_transition | +0.0 | 1.00 | 1 | low | last-line fill 0% |
| c046 | min.tex:53 | sentence_descriptive | +0.0 | 1.80 | 2 | medium | last-line fill 17%; next block is a paragraph (pullable) |
| c049 | min.tex:56 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c050 | min.tex:61 | sentence_descriptive | +0.0 | 0.80 | 2 | low | last-line fill 0%; float risk 0.40 |
| c051 | min.tex:61 | sentence_descriptive | +0.0 | 0.80 | 2 | low | last-line fill 0%; float risk 0.40 |
| c052 | min.tex:62 | sentence_descriptive | +0.0 | 0.80 | 2 | low | last-line fill 0%; float risk 0.40 |
| c053 | min.tex:62 | sentence_descriptive | +0.0 | 0.80 | 2 | low | last-line fill 0%; float risk 0.40 |
| c054 | min.tex:65 | sentence_claim | +0.0 | 1.44 | 4 | low | last-line fill 16%; next block is a paragraph (pullable); float risk 0.40 |
| c055 | min.tex:67 | sentence_descriptive | +0.0 | 1.44 | 2 | medium | last-line fill 16%; next block is a paragraph (pullable); float risk 0.40 |
| c056 | min.tex:70 | discourse_transition | +0.0 | -0.50 | 1 | medium | last-line fill 16% |
| c057 | min.tex:71 | discourse_transition | +0.0 | -0.50 | 1 | medium | last-line fill 16% |
| c058 | min.tex:70 | discourse_transition | +0.0 | -0.50 | 1 | medium | last-line fill 16% |
| c059 | min.tex:68 | sentence_descriptive | +0.0 | 1.80 | 2 | low | last-line fill 16%; next block is a paragraph (pullable) |
| c060 | min.tex:70 | sentence_descriptive | +0.0 | -0.50 | 2 | low | last-line fill 16% |
| c061 | min.tex:71 | sentence_descriptive | +0.0 | -0.50 | 2 | low | last-line fill 16% |
| c062 | min.tex:74 | sentence_descriptive | +0.0 | 1.80 | 2 | medium | last-line fill 27%; next block is a paragraph (pullable) |
| c063 | min.tex:74 | sentence_descriptive | +0.0 | 1.80 | 2 | medium | last-line fill 27%; next block is a paragraph (pullable) |
| c064 | min.tex:75 | sentence_descriptive | +0.0 | 1.80 | 2 | medium | last-line fill 27%; next block is a paragraph (pullable) |
| c065 | min.tex:76 | sentence_descriptive | +0.0 | 1.80 | 2 | medium | last-line fill 27%; next block is a paragraph (pullable) |
| c066 | min.tex:76 | sentence_descriptive | +0.0 | 1.80 | 2 | medium | last-line fill 27%; next block is a paragraph (pullable) |
| c067 | min.tex:76 | sentence_descriptive | +0.0 | 1.80 | 2 | medium | last-line fill 27%; next block is a paragraph (pullable) |
| c068 | min.tex:76 | sentence_claim | +0.0 | 1.80 | 4 | medium | last-line fill 27%; next block is a paragraph (pullable) |
| c069 | min.tex:77 | discourse_transition | +0.0 | -0.50 | 1 | medium | last-line fill 31% |
| c070 | min.tex:78 | discourse_transition | +0.0 | -0.50 | 1 | medium | last-line fill 31% |
| c071 | min.tex:78 | sentence_descriptive | +0.0 | -0.50 | 2 | low | last-line fill 31% |
| c072 | min.tex:83 | discourse_transition | +0.0 | 1.44 | 1 | medium | last-line fill 21%; next block is a paragraph (pullable); float risk 0.40 |
| c073 | min.tex:83 | sentence_descriptive | +0.0 | 1.44 | 2 | medium | last-line fill 21%; next block is a paragraph (pullable); float risk 0.40 |
| c074 | min.tex:83 | sentence_claim | +0.0 | 1.44 | 4 | low | last-line fill 21%; next block is a paragraph (pullable); float risk 0.40 |
| c075 | min.tex:86 | sentence_descriptive | +0.0 | 1.44 | 2 | medium | last-line fill 21%; next block is a paragraph (pullable); float risk 0.40 |
| c076 | min.tex:89 | sentence_descriptive | +0.0 | 1.44 | 2 | medium | last-line fill 15%; next block is a paragraph (pullable); float risk 0.40 |
| c077 | min.tex:89 | sentence_descriptive | +0.0 | 1.44 | 2 | medium | last-line fill 15%; next block is a paragraph (pullable); float risk 0.40 |
| c078 | min.tex:89 | sentence_descriptive | +0.0 | 1.44 | 2 | medium | last-line fill 15%; next block is a paragraph (pullable); float risk 0.40 |
| c079 | min.tex:91 | sentence_claim | +0.0 | 1.44 | 4 | medium | last-line fill 15%; next block is a paragraph (pullable); float risk 0.40 |
| c080 | min.tex:91 | sentence_claim | +0.0 | 1.44 | 4 | medium | last-line fill 15%; next block is a paragraph (pullable); float risk 0.40 |
| c081 | min.tex:91 | sentence_claim | +0.0 | 1.44 | 4 | medium | last-line fill 15%; next block is a paragraph (pullable); float risk 0.40 |
| c082 | min.tex:91 | sentence_claim | +0.0 | 1.44 | 4 | medium | last-line fill 15%; next block is a paragraph (pullable); float risk 0.40 |
| c083 | min.tex:92 | sentence_claim | +0.0 | 0.08 | 4 | medium | last-line fill 7%; float risk 0.40 |
| c084 | min.tex:92 | sentence_claim | +0.0 | 0.08 | 4 | medium | last-line fill 7%; float risk 0.40 |
| c085 | min.tex:92 | sentence_claim | +0.0 | 0.08 | 4 | medium | last-line fill 7%; float risk 0.40 |
| c086 | min.tex:93 | sentence_claim | +0.0 | 0.08 | 4 | medium | last-line fill 7%; float risk 0.40 |
| c087 | min.tex:93 | sentence_claim | +0.0 | 0.08 | 4 | medium | last-line fill 7%; float risk 0.40 |
| c088 | min.tex:93 | sentence_descriptive | +0.0 | 0.08 | 2 | medium | last-line fill 7%; float risk 0.40 |
| c089 | min.tex:94 | sentence_claim | +0.0 | 0.08 | 4 | medium | last-line fill 7%; float risk 0.40 |
| c090 | min.tex:94 | sentence_claim | +0.0 | 0.08 | 4 | medium | last-line fill 7%; float risk 0.40 |
| c091 | min.tex:102 | discourse_transition | +0.0 | 2.40 | 1 | medium | last-line fill 1%; next block is a paragraph (pullable) |
| c093 | min.tex:101 | discourse_transition | +0.0 | 2.40 | 1 | medium | last-line fill 1%; next block is a paragraph (pullable) |
| c094 | min.tex:102 | sentence_descriptive | +0.0 | 2.40 | 2 | medium | last-line fill 1%; next block is a paragraph (pullable) |
| c096 | min.tex:106 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c097 | min.tex:109 | discourse_transition | +0.0 | 1.50 | 1 | medium | on last page; last-line fill 20% |
| c098 | min.tex:108 | discourse_transition | +0.0 | 1.50 | 1 | medium | on last page; last-line fill 20% |
| c099 | min.tex:109 | discourse_transition | +0.0 | 1.50 | 1 | medium | on last page; last-line fill 20% |
| c100 | min.tex:107 | discourse_transition | +0.0 | 1.00 | 1 | low | last-line fill 0% |
| c101 | min.tex:110 | discourse_transition | +0.0 | 1.50 | 1 | medium | on last page; last-line fill 20% |
| c102 | min.tex:106 | section_opening | +0.0 | 1.00 | 3 | low | last-line fill 0% |
| c103 | min.tex:107 | sentence_descriptive | +0.0 | 1.00 | 2 | low | last-line fill 0% |
| c104 | min.tex:108 | sentence_descriptive | +0.0 | 1.50 | 2 | medium | on last page; last-line fill 20% |
| c105 | min.tex:109 | sentence_descriptive | +0.0 | 1.50 | 2 | medium | on last page; last-line fill 20% |
| c106 | min.tex:109 | sentence_descriptive | +0.0 | 1.50 | 2 | medium | on last page; last-line fill 20% |
| c107 | min.tex:110 | sentence_descriptive | +0.0 | 1.50 | 2 | medium | on last page; last-line fill 20% |
| c108 | min.tex:113 | sentence_descriptive | +0.0 | 3.80 | 2 | low | on last page; last-line fill 76%; next block is a paragraph (pullable) |
| c109 | min.tex:115 | discourse_transition | +0.0 | 1.50 | 1 | medium | on last page; last-line fill 26% |
| c110 | min.tex:116 | discourse_transition | +0.0 | 1.50 | 1 | medium | on last page; last-line fill 26% |
| c111 | min.tex:117 | discourse_transition | +0.0 | 1.50 | 1 | medium | on last page; last-line fill 26% |
| c112 | min.tex:114 | discourse_transition | +0.0 | 1.50 | 1 | medium | on last page; last-line fill 26% |
| c114 | min.tex:114 | sentence_descriptive | +0.0 | 1.50 | 2 | medium | on last page; last-line fill 26% |
| c115 | min.tex:114 | sentence_claim | +0.0 | 1.50 | 4 | medium | on last page; last-line fill 26% |
| c116 | min.tex:115 | sentence_descriptive | +0.0 | 1.50 | 2 | medium | on last page; last-line fill 26% |
| c117 | min.tex:116 | sentence_descriptive | +0.0 | 1.50 | 2 | low | on last page; last-line fill 26% |
| c118 | min.tex:117 | sentence_descriptive | +0.0 | 1.50 | 2 | medium | on last page; last-line fill 26% |
| c047 | min.tex:54 | sentence_descriptive | -1.0 | -0.50 | 2 | medium | last-line fill 100% |
| c048 | min.tex:55 | sentence_descriptive | -1.0 | -0.50 | 2 | medium | last-line fill 100% |

