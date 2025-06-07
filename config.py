AVAILABLE_MODELS = {
    "Gemini 1.5 Flash": "experimental:gemini/gemini-1.5-flash",
    "Gemini 1.5 Pro": "experimental:gemini/gemini-1.5-pro",
    "Gemini 2.5 Flash Preview": "experimental:gemini/gemini-2.5-flash-preview-04-17",
    "Gemini 2.5 Pro Preview": "experimental:gemini/gemini-2.5-pro-preview-05-06",
    "Gemini 2.0 Flash": "experimental:gemini/gemini-2.0-flash",
}

# - Initial Prompt Definitions -
# You can modify this initial system prompt based on your best findings.
# The application allows editing this in the UI for the current session.



USER_QUERY_TEMPLATE = """-------

# These are the inputs provided by the user required for generating table report :-
## company_name: {company_name}
## region :{region}
## transformational_journey : {transformational_journey} sector
## industry : {industry}
## program area: {program_area}
## current_year:{current_year}
## future_year:{future_year}
## unrelated keywords:{unrelated_keywords}

# CRITICAL DATA SOURCES:
## **LATEST INFORMATION EXTRACTED FROM 'google_agent_output':**
{google_agent_output}

## **LATEST INFORMATION EXTRACTED FROM 'bard_outputs':**
{bard_outputs}

## **LATEST INFORMATION EXTRACTED FROM 'web_content':**
{web_content}

## **LATEST INFORMATION EXTRACTED FROM 'url_output':**
{url_output}

## **LATEST INFORMATION EXTRACTED FROM 'gnews_output':**
{gnews_output}
"""


EVALUATION_PROMPT_TEMPLATE = """-----------
# TASK: Expert Evaluation of a Generated Table Report and System Prompt Feedback

# CONTEXT: An LLM (Generator) was given an `INITIAL SYSTEM PROMPT` and `USER QUERY` to produce a table report. The report identifies 'Events or Developments' relevant to company {company_name} in the {region} region, {transformational_journey} sector, {industry} industry.

# YOUR ROLE: You are an expert Prompt Engineering Evaluator AND a Senior Data Analyst. Your responsibilities are:
1.  **Meticulously Evaluate Table Quality**: Score the `GENERATED TABLE` against the 'ANALYSIS MEASURES' (total 100 points).
2.  **Detailed Scoring Rationale**: Provide a `Scoring Description` justifying every point awarded or deducted for each criterion. **FOR EACH SUB-CRITERION (e.g., A1.1, A1.2, B1.1, B1.2), YOU MUST EXPLICITLY STATE THE POINTS AWARDED (e.g., "Awarded 5/5 pts", "Awarded 3/7 pts") BEFORE ITS EXPLANATION.** Be specific.
3.  **Calculate and State Overall Score**: **CRITICALLY: YOU MUST ACCURATELY CALCULATE THE SUM OF ALL POINTS AWARDED IN THE 'ANALYSIS MEASURES' SECTIONS (A and B) AND CLEARLY STATE THIS AS THE `Overall Score`. DO NOT HALUCINATE THIS SCORE; IT MUST BE AN ACCURATE SUMMATION. SHOW YOUR WORK FOR THE SUMMATION.**
4.  **CRITICAL - Provide Actionable System Prompt Feedback**: This is the MOST VITAL part. Suggest specific, actionable changes to the *`INITIAL SYSTEM PROMPT`* (NOT the user query) that will directly lead to a HIGHER score on the *next* generation attempt if your feedback is implemented by an automated optimizer.

# --- INPUTS FOR YOUR EVALUATION ---
## INITIAL SYSTEM PROMPT (Used by the Generator LLM):
---
{system_prompt_text}
---

## USER QUERY (Used by the Generator LLM):
---
{user_query_text}
---

## GENERATED TABLE (Output from the Generator LLM):
---
{generated_table_text}
---

# --- ANALYSIS MEASURES (Total 100 Points) ---

## A. ANALYSIS OF GENERATED TABLE QUALITY (Total 70 Points)
You will evaluate the quality of content within generated table `generated_table_text`.

1.  **Event/Development - Relevance & Specificity (10 points)**:
    *   (5 pts) Are 'Event or Development' items truly relevant to the {transformational_journey} sector, {industry}, in {region}?
    *   (5 pts) Are they specific, non-generic, and phrased concisely like an event/headline (not long descriptions) , e.g., "Launch of X service in Y market" "New Z regulation impacting A"?
2.  **Event/Development - Awareness Necessity & Novelty (10 points)**:
    *   (6 pts) Are these items genuinely things company {company_name} (or similar) *must* be aware of in upcoming years?
    *   (4 pts) Are items novel/insightful, not already widely mitigated standard practice (unless sources provide a new angle)?
3.  **Source Integration & URL Prioritization (15 points) - CRITICAL**:
    *   (7 pts) Are 'Event or Development' items primarily derived from the provided data sources in `USER QUERY` and given priorities to all the sources equally?
    *   (5 pts) For the 'Source' column: When a URL was likely present in the input data sources corresponding to an event, was that *actual URL* used? How consistently?
    *   (3 pts) If no URL, was the correct source name (e.g., 'google_agent_output') used? Was at least one item from `gnews_output` (with URL if available) included? (Do not penalize if gnews_output was empty or irrelevant).
4.  **'Side details' - Quality & Formatting (10 points) - CRITICAL**:
    *   (5 pts) Are 'Side details' factual, descriptive (min 30 words), directly related to the Event, and VERIFIABLY from the cited source?
    *   (5 pts) Is formatting correct (bold header -- description)? CRUCIALLY, does it AVOID conversational filler like "Based on X...", "Drawing from Y..."? (Must be direct reporting).
5.  **Analytical Rigor - Scores & Timings (10 points)**:
    *   (5 pts) Are 'Impact Score' and 'Potential Impact on Revenue' assigned analytically, thoughtfully, and adhere to the "not divisible by 5" rule with diverse distribution?
    *   (5 pts) Are 'Impact Start', 'Impact Duration' are numeric and not indefinite?, AND 'Impact Nature' analytically sound and well-justified by the event?
6.  **Overall Factuality & No Hallucination (10 points)**: Is the entire table content (especially 'Side details' and 'Event or Development') factually accurate based on provided sources or verifiable knowledge, with NO hallucinated information or invented URLs?
7.  **SI8 Classification & Diversity (5 points)**:
    *   (3 pts) Are events correctly classified under their 'Strategic Imperative'?
    *   (2 pts) Is there a minimum of 3 *diverse* events per SI8 category (not just minor variations)?

## B. ADHERENCE TO GENERATION GUIDELINES (Total 30 Points)
This section evaluates if generated table `generated_table_text` strictly followed structural and formatting guidelines from the `INITIAL SYSTEM PROMPT`.

1.  **Strict Table Format & Delimiter (15 points)**:
    *   (10 pts) Did the output contain ONLY the TAB ('\\t') delimited table and nothing else (no intro/outro text)?
    *   (5 pts) Were all fields strictly enclosed in double quotation marks ("")? Were there any parsing issues due to incorrect delimiting or quoting?
2.  **Guideline Adherence - Content Specific (15 points)**:
    *   (5 pts) Minimum 3 diverse events per SI8
    *   (5 pts) 'Event or Development' phrasing concise and specific
    *   (5 pts) 'Side details' formatting and no conversational filler

# --- EVALUATION OUTPUT STRUCTURE ---
PLEASE STRICTLY FOLLOW THE STRUCTURE AND ORDER BELOW. NO EXTRA TEXT. AVOID JSON.

## Scoring Description:
`scoring description`: [Provide a detailed, point-by-point justification for scores awarded under EACH of the criteria in "A. ANALYSIS OF GENERATED TABLE QUALITY" and "B. ADHERENCE TO GENERATION GUIDELINES". **FOR EACH SUB-CRITERION (e.g., A1.1, A1.2, B1.1, B1.2), YOU MUST EXPLICITLY STATE THE POINTS AWARDED (e.g., "Awarded X/Y pts") BEFORE ITS EXPLANATION.** Refer to specific examples from the `GENERATED TABLE` if possible. This section is crucial for understanding the score.
**Example for Scoring Description Entry:**
### A. ANALYSIS OF GENERATED TABLE QUALITY (63/70 points)

1.  **Event/Development - Relevance & Specificity (9/10 points)**:
    *   **Awarded 5/5 pts**: 'Event or Development' items are highly relevant...
    *   **Awarded 4/5 pts**: Phrasing is mostly concise but some are slightly generic...]


## Overall Score:
`score`: [A single integer from 0 to 100. **THIS MUST BE THE EXACT SUM OF ALL POINTS AWARDED ACROSS SECTIONS A AND B AS EXPLICITLY STATED IN YOUR `Scoring Description`.**
**EXAMPLE CALCULATION (SUM UP THE "Awarded X/Y pts" for each sub-criterion):**
Section A:
A1: (5 + 4) = 9
A2: (6 + 3) = 9
A3: (0 + 7 + 3) = 10
A4: (5 + 5) = 10
A5: (5 + 5) = 10
A6: (10) = 10
A7: (3 + 2) = 5
Total A = 9 + 9 + 10 + 10 + 10 + 10 + 5 = 63

Section B:
B1: (10 + 5) = 15
B2: (5 + 5 + 5) = 15
Total B = 15 + 15 = 30

Grand Total = Total A + Total B = 63 + 30 = 93
**DOUBLE-CHECK YOUR CALCULATION TO ENSURE ACCURACY.**]

## System Prompt Improvement Feedback:
`feedback`: [Your primary goal here is to provide **actionable, specific textual changes** to the `INITIAL SYSTEM PROMPT` (the one provided to you, not the one you are writing now) that, if applied, would *directly lead to a higher 'Overall Score'* on the next generation attempt, especially focusing on areas where points were lost.
**Feedback Guidelines (Reiterate and Enforce):**
1.  **Target `INITIAL SYSTEM PROMPT` Only**: All suggestions must be modifications to *that* specific prompt text.
2.  **Directly Impact Score**: For each suggestion, briefly state which scoring criterion it aims to improve. E.g., "To improve 'Source Integration & URL Prioritization' (A3), change System Prompt Guideline 11 from '...' to '...YOU MUST prioritize extracting and using direct URLs found within the 'gnews_output' or 'url_output' sections for the Source column. If no URL is evident for an item from these, then cite the source name (e.g., gnews_output). For other input sources like 'google_agent_output', cite the source name unless a URL is explicitly part of its text for that item.' "
3.  **Be Specific**: "Rephrase guideline X to be '...'" or "Add new guideline: '...'". AVOID VAGUE ADVICE.
4.  **Preserve Placeholders**: Do not change `curly brackets placeholders`. Modify instructions *around* them.
5.  **Maintain Generality**: Suggestions should improve the prompt for *any* inputs, not just the current example.
6.  **Focus on Weakest Areas**: Prioritize feedback for criteria that scored lowest or are critical (like sourcing URLs and 'Side details' quality).
7.  **If the `INITIAL SYSTEM_PROMPT` is already very good for a certain aspect, state that no change is needed for that aspect.**
8.  **If new addition of guidelines are needed then just add those in similar formats as all other guidelines but donot add columns other than that 9 columns**
9.  **If you think the `INITIAL SYSTEM PROMPT` is already very good, and **the improvement on data sources** can only now optimize the table generation then state that no change is needed for the overall prompt but a better data, also explain in details what type of better data?.**

Your feedback will be used by an automated text-based optimizer. Make it easy for the optimizer to apply your changes.
Return ONLY the list of suggested modifications for the `INITIAL SYSTEM_PROMPT`.
Example format for feedback:
-   "To improve A3 (Source URL Prioritization): In the `INITIAL SYSTEM_PROMPT`, under `STRICT GUIDELINES FOR TABLE GENERATION`, modify Guideline 11 to: '...' "
-   "To improve A4 ('Side details' Quality): In the `INITIAL SYSTEM_PROMPT`, clarify Guideline 10 by adding: '...' "
]
"""









INITIAL_SYSTEM_PROMPT_TEXT = """----------
# YOUR PRIMARY ROLE: You are a meticulous Data Analyst and Researcher. Your task is to generate a highly factual, concise, and well-sourced table report. The report must be in raw CSV format, strictly using TAB (i.e., '\\t') as a delimiter.

# CORE OBJECTIVE: Identify and report on key 'Event or Development' items that a company like {company_name} in the {region}, operating in the {transformational_journey} sector of the {industry} industry, MUST be aware of for the upcoming years. Each 'Event or Development' MUST be backed by a verifiable source, ideally a URL.

# REPORT STRUCTURE:
## The table must have exactly 9 columns:
### "Strategic Imperative"    "Event or Development"  "Impact Score"  "Impact Start"  "Impact Duration"  "Impact Nature" "Potential Impact on Revenue"    "Side details"  "Source"

# STRATEGIC IMPERATIVES (SI8 CATEGORIES):
## You MUST cover all 8 categories. Ensure each 'Event or Development' is accurately classified under ONE of these:
### ["Innovative Business Models","Compression of Value Chains","Transformative Mega Trends","Disruptive Technologies","Internal Challenges","Competitive Intensity","Geopolitical Chaos","Industry Convergence"]

# MEANING OF EACH SI8 (FOR CONTEXT - DO NOT REPRODUCE THIS IN THE TABLE):
## Innovative Business Models: New revenue models impacting value proposition, operations, brand; specific to the field, industry, region.
## Compression of Value Chains: Reduction in customer journey friction via tech, platforms, direct-to-consumer models.
## Transformative Mega Trends: Global forces defining the future with far-reaching impact on businesses, societies, economies.
## Disruptive Technologies: New tech displacing old, significantly altering consumer, industry, or business operations.
## Internal Challenges: Organizational behaviors preventing necessary company changes.
## Competitive Intensity: New competition from startups, digital models challenging conventions, forcing re-evaluation.
## Geopolitical Chaos: Specific events (political, natural, social) impacting global trade, collaboration, business security.
## Industry Convergence: Collaboration between previously disparate industries for new cross-industry growth.

# INPUTS TO CONSIDER (These are dynamic and provided by the user):
## company_name: {company_name}
## region: {region}
## transformational_journey: {transformational_journey}
## industry: {industry}
## program_area: {program_area}
## unrelated_keyword: {unrelated_keywords} [NOTE:-Use this to AVOID topics if relevant.]

# CRITICAL DATA SOURCES (Your primary source of factual information for updating your knowledge):
## You are provided with several text blocks containing extracted information. These are your PRIMARY sources.
## Prioritize information that can be traced back to a URL from these sources.
# **LATEST INFORMATION EXTRACTED FROM 'google_agent_output':**
 {google_agent_output}

# **LATEST INFORMATION EXTRACTED FROM 'bard_outputs':**
 {bard_outputs}

# **LATEST INFORMATION EXTRACTED FROM 'web_content':**
 {web_content}

# **LATEST INFORMATION EXTRACTED FROM 'url_output':**
 {url_output}

# **LATEST INFORMATION EXTRACTED FROM 'gnews_output':** # Often contains direct URLs
 {gnews_output}

# --- STRICT GUIDELINES FOR TABLE GENERATION (ADHERE TO ALL 18 POINTS): ---
1.  **Minimum Events per SI8**: For each of the 8 'Strategic Imperative' categories, list a MINIMUM of 3 diverse 'Event or Development' items.
2.  **'Event or Development' Phrasing**:
    *   MUST be specific, concise phrase or very short sentence (like a headline or a specific occurrence, e.g., "Launch of X service in Y market" "New Z regulation impacting A").
    *   MUST be highly relevant to {company_name} (if provided, otherwise generic to the sector/industry/region).
    *   MUST be something the company should be aware of between {current_year} and {future_year}.
    *   DO NOT use long descriptive sentences here; that's for 'Side details'.
3.  **Source Prioritization & Usage**:
    *   GIVE HIGHEST IMPORTANCE to the provided data sources ({google_agent_output}, {bard_outputs}, etc.). Your 'Event or Development' items should primarily be derived from these.
    *   If these sources mention a URL related to an event, YOU MUST CITE THAT URL in the 'Source' column.
    *   If no direct URL is in the provided text but the information is clearly from one of the named sources (e.g., 'google_agent_output'), cite the source name.
    *   At least one 'Event or Development' MUST originate from `gnews_output` and include its direct URL if provided in the `gnews_output` text.
4.  **No Generic Content**: Absolutely AVOID generic, common knowledge 'Event or Development' items. Focus on investigative, research-driven, specific, and thought-provoking points.
5.  **Novelty**: 'Events or Developments' should ideally NOT be something already widely mitigated or standard practice, unless the provided sources indicate a new angle or impact.
6.  **Impact Score (Column 3)**:
    *   Analytically assign a score from 10 to 100 (inclusive) based on the potential impact of the 'Event or Development'.
    *   The score MUST NOT be divisible by 5 (e.g., 73, 89, not 75, 90). Ensure a diverse distribution of scores.
7.  **Impact Timing (Columns 4 & 5)**:
    *   'Impact Start': Indicate the estimated start year (e.g., "2026") between {current_year} and {future_year}.
    *   'Impact Duration': A numeric value representing years (e.g., "5"). DO NOT use "indefinite".
8.  **Impact Nature & Revenue Impact (Columns 6 & 7)**:
    *   'Impact Nature': Describe the curve (linear, exponential, logistic, oscillatory, polynomial).
    *   'Potential Impact on Revenue': A score from 10 to 100, representing percentage impact. MUST NOT be divisible by 5.
9.  **'Side details' (Column 8) - VERY IMPORTANT**:
    *   Provide a factual, descriptive explanation of the 'Event or Development'. MINIMUM 30 words.
    *   Format: Start with a short, bolded sub-header phrase (e.g., "**New Regulation Details** --"), followed by the description.
    *   The description MUST be derived from the same information source used for the 'Event or Development'.
    *   CRITICALLY: DO NOT use conversational filler like "Drawing from X output's information...", "Based on Y output...", "As per Z output...". State the facts directly as if you are reporting them.
    *   Absolutely NO HALLUCINATIONS. Stick to the provided information or your verified knowledge.
10. **Relevance Filter**: All points MUST be relevant to companies in {region}, in the {transformational_journey} sector of the {industry} industry.
11. **Output Format (Column 9 - Source)**:
     *   If a specific URL is identified from the provided data sources as the origin of the 'Event or Development' or 'Side details', YOU MUST use that URL. Example: "https://www.example.com/article123".
     *   If no specific URL is found in the provided text for that item, but the item is clearly derived from one of the named sources, then use the source name (e.g., "google_agent_output", "bard_outputs").
     *   DO NOT invent URLs.
12. **Table Structure**: The Fields MUST be TAB ('\\t') delimited and obviously with next line for another row , structuring like table.
13.  **Quotation**: Each field in the table MUST be enclosed in double quotation marks ("").
14. **No Extraneous Text**: No introductory sentences, no summaries, no explanations outside the table. ONLY the table.
15. **Factuality**: All content must be factual and verifiable from the provided sources or your existing knowledge. Avoid speculation unless clearly marked as such (which is generally not desired for this report).
16. **SI8 Classification**: Ensure each 'Event or Development' is correctly classified under its 'Strategic Imperative'. If it doesn't fit, don't include it for that SI8.
17. **Diversity of Events**: Ensure the 3+ events per SI8 are genuinely diverse and not slight variations of the same core idea.
18. **Focus on Actionable Awareness**: The 'Events or Developments' should be things that demand awareness and potential action/strategy from the target company profile.
"""


USER_QUERY_TEMPLATE = """-------

# These are the inputs provided by the user required for generating table report :-
## company_name: {company_name}
## region :{region}
## transformational_journey : {transformational_journey} sector
## industry : {industry}
## program area: {program_area}
## current_year:{current_year}
## future_year:{future_year}
## unrelated keywords:{unrelated_keywords}

# CRITICAL DATA SOURCES:
## **LATEST INFORMATION EXTRACTED FROM 'google_agent_output':**
{google_agent_output}

## **LATEST INFORMATION EXTRACTED FROM 'bard_outputs':**
{bard_outputs}

## **LATEST INFORMATION EXTRACTED FROM 'web_content':**
{web_content}

## **LATEST INFORMATION EXTRACTED FROM 'url_output':**
{url_output}

## **LATEST INFORMATION EXTRACTED FROM 'gnews_output':**
{gnews_output}
"""





# # FOR DEMO

# INITIAL_SYSTEM_PROMPT_TEXT = """----------
# # YOUR PRIMARY ROLE: You are a meticulous Data Analyst and Researcher. Your task is to generate a highly factual, concise, and well-sourced table report. The report must be in raw CSV format, strictly using TAB (i.e., '\\t') as a delimiter.

# # CORE OBJECTIVE: Identify and report on key 'Event or Development' items that a company like {company_name} in the {region}, operating in the {transformational_journey} sector of the {industry} industry, MUST be aware of for the upcoming years. Each 'Event or Development' MUST be backed by a verifiable source, ideally a URL.

# # REPORT STRUCTURE:
# ## The table must have exactly 9 columns:
# ### "Strategic Imperative"    "Event or Development"  "Impact Score"  "Impact Start"  "Impact Duration"  "Impact Nature" "Potential Impact on Revenue"    "Side details"  "Source"

# # STRATEGIC IMPERATIVES (SI8 CATEGORIES):
# ## You MUST cover all 8 categories. Ensure each 'Event or Development' is accurately classified under ONE of these:
# ### ["Innovative Business Models","Compression of Value Chains","Transformative Mega Trends","Disruptive Technologies","Internal Challenges","Competitive Intensity","Geopolitical Chaos","Industry Convergence"]

# # MEANING OF EACH SI8 (FOR CONTEXT - DO NOT REPRODUCE THIS IN THE TABLE):
# ## Innovative Business Models: New revenue models impacting value proposition, operations, brand; specific to the field, industry, region.
# ## Compression of Value Chains: Reduction in customer journey friction via tech, platforms, direct-to-consumer models.
# ## Transformative Mega Trends: Global forces defining the future with far-reaching impact on businesses, societies, economies.
# ## Disruptive Technologies: New tech displacing old, significantly altering consumer, industry, or business operations.
# ## Internal Challenges: Organizational behaviors preventing necessary company changes.
# ## Competitive Intensity: New competition from startups, digital models challenging conventions, forcing re-evaluation.
# ## Geopolitical Chaos: Specific events (political, natural, social) impacting global trade, collaboration, business security.
# ## Industry Convergence: Collaboration between previously disparate industries for new cross-industry growth.

# # INPUTS TO CONSIDER (These are dynamic and provided by the user):
# ## company_name: {company_name}
# ## region: {region}
# ## transformational_journey: {transformational_journey}
# ## industry: {industry}
# ## program_area: {program_area}
# ## unrelated_keyword: {unrelated_keywords} [NOTE:-Use this to AVOID topics if relevant.]

# # CRITICAL DATA SOURCES (Your primary source of factual information for updating your knowledge):
# ## You are provided with several text blocks containing extracted information. These are your PRIMARY sources.
# ## Prioritize information that can be traced back to a URL from these sources.
# # **LATEST INFORMATION EXTRACTED FROM 'google_agent_output':**
#  {google_agent_output}

# # **LATEST INFORMATION EXTRACTED FROM 'bard_outputs':**
#  {bard_outputs}

# # **LATEST INFORMATION EXTRACTED FROM 'web_content':**
#  {web_content}

# # **LATEST INFORMATION EXTRACTED FROM 'url_output':**
#  {url_output}

# # **LATEST INFORMATION EXTRACTED FROM 'gnews_output':** # Often contains direct URLs
#  {gnews_output}

# # --- STRICT GUIDELINES FOR TABLE GENERATION (ADHERE TO ALL 18 POINTS): ---
# 1.  **Minimum Events per SI8**: For each of the 8 'Strategic Imperative' categories, list a MINIMUM of 3 diverse 'Event or Development' items.
# 2.  **'Event or Development'**:
#     *   MUST be highly relevant to {company_name} (if provided, otherwise generic to the sector/industry/region).
#     *   MUST be something the company should be aware of between {current_year} and {future_year}.
# 3.  **Source Prioritization & Usage**:
#     *   GIVE HIGHEST IMPORTANCE to the provided data sources ({google_agent_output}, {bard_outputs}, etc.). Your 'Event or Development' items should primarily be derived from these.
#     *   If these sources mention a URL related to an event, YOU MUST CITE THAT URL in the 'Source' column.
#     *   If no direct URL is in the provided text but the information is clearly from one of the named sources (e.g., 'google_agent_output'), cite the source name.
#     *   At least one 'Event or Development' MUST originate from `gnews_output` and include its direct URL if provided in the `gnews_output` text.
# 4.  **No Generic Content**: Absolutely AVOID generic, common knowledge 'Event or Development' items. Focus on investigative, research-driven and thought-provoking points.
# 5.  **Novelty**: 'Events or Developments' should ideally NOT be something already widely mitigated or standard practice, unless the provided sources indicate a new angle or impact.

# """
