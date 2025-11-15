# Content Policy & Safety Guidelines

## Purpose

This document defines Zapcut's content safety rules, brand compliance requirements, and moderation policies. These rules are **non-negotiable** and enforced at multiple layers: orchestrator agent, safety validation agent, and prompt synthesis.

All content must be **brand-safe, legally compliant, and suitable for commercial use**.

---

## Prohibited Content (Hard Blocks)

### 1. Violence & Dangerous Content
**Status**: ❌ **BLOCKED**

#### Not Allowed:
- Violence, gore, blood, injuries
- Weapons (guns, knives, explosives)
- Physical fights or abuse
- Self-harm, suicide references
- Dangerous stunts (reckless driving, cliff jumping, fire stunts)
- Threatening behavior or intimidation

#### Why:
- Brand safety: Advertisers avoid violent content
- Platform policies: Social networks ban graphic violence
- Legal risk: Liability for promoting dangerous behavior

#### Examples:
- ❌ "Action scene with car crash and explosion"
- ❌ "Person holding a gun while drinking our product"
- ❌ "Extreme parkour jumping between buildings"

---

### 2. Sexual Content & Nudity
**Status**: ❌ **BLOCKED**

#### Not Allowed:
- Nudity (partial or full)
- Sexual acts or suggestive poses
- Sexualized depictions of any person
- Revealing clothing (bikinis, lingerie) in non-contextual settings
- Sexual innuendo in scripts

#### Why:
- Brand safety: Most advertisers require G/PG content
- Platform policies: Strict on sexual content
- Audience appropriateness: Brands target all ages

#### Exceptions:
- ✅ Swimwear in beach/pool context (if brand-appropriate, e.g., swimwear brand)
- ✅ Fitness apparel in gym setting

#### Examples:
- ❌ "Model in lingerie holding product"
- ❌ "Romantic scene with kissing"
- ✅ "Person in activewear doing yoga"

---

### 3. Drugs, Alcohol, Tobacco
**Status**: ❌ **BLOCKED** (with exceptions)

#### Not Allowed:
- Illegal drugs or drug paraphernalia
- Smoking (cigarettes, vaping, cannabis)
- Alcohol consumption (unless explicitly client's product + legal region)
- Drug references or slang

#### Why:
- Legal restrictions: Many countries ban drug/alcohol ads
- Platform policies: Strict limitations on substance ads
- Brand safety: Most brands avoid association

#### Exceptions:
- ✅ Alcohol brands advertising their own product (must specify legal region, age-gate, responsible drinking)
- ✅ CBD products (if legal in target region, with disclaimers)

#### Examples:
- ❌ "Friends drinking beer at party"
- ❌ "Person vaping while using product"
- ✅ "Responsible wine tasting event (for wine brand, 21+ audience)"

---

### 4. Hate Speech & Extremism
**Status**: ❌ **BLOCKED**

#### Not Allowed:
- Hate speech against any group (race, religion, gender, sexuality, etc.)
- Extremist symbols or references
- Discriminatory messaging
- Political propaganda
- Harassment or bullying

#### Why:
- Legal risk: Hate speech laws in many countries
- Brand damage: Irreversible reputation harm
- Platform policies: Zero tolerance

#### Examples:
- ❌ Any content targeting protected groups
- ❌ Political campaign messaging
- ❌ Religious extremism

---

### 5. Deepfakes & Real People
**Status**: ❌ **BLOCKED**

#### Not Allowed:
- Depictions of real celebrities, influencers, politicians
- Likeness of public figures without consent
- Voice imitation of real people
- Deepfake technology to impersonate anyone
- Using real people's images without permission

#### Why:
- Legal risk: Right of publicity, defamation lawsuits
- Ethical concerns: Consent and authenticity
- Platform policies: Ban on deepfakes

#### Requirement:
- **All humans in generated videos must be synthetic and non-identifiable**
- No real faces, voices, or likenesses

#### Examples:
- ❌ "Elon Musk endorsing our product"
- ❌ "Create a video with [uploaded photo of me]"
- ✅ "Generic professional person in office setting"

---

### 6. Copyright & Trademark Violations
**Status**: ❌ **BLOCKED**

#### Not Allowed:
- Copyrighted characters (Mickey Mouse, Spider-Man, etc.)
- Trademarked brands (unless client's own brand)
- Movie/TV references without license
- Competitor logos or products
- Licensed music (use royalty-free or Suno-generated only)
- Copied visual styles from identifiable copyrighted works

#### Why:
- Legal risk: Copyright infringement lawsuits
- Platform policies: DMCA takedowns
- Competitive fairness: No free-riding on others' IP

#### Examples:
- ❌ "Create a Star Wars-style space battle"
- ❌ "Show a McDonald's restaurant in background"
- ❌ "Use the Marvel Cinematic Universe aesthetic"
- ✅ "Futuristic space scene with original spacecraft"

---

### 7. Misinformation & False Claims
**Status**: ❌ **BLOCKED**

#### Not Allowed:
- False health claims ("Cures cancer", "Guaranteed weight loss")
- Misleading product claims ("Best in the world" without evidence)
- Financial scams or get-rich-quick schemes
- Fake reviews or testimonials
- Misleading before/after transformations

#### Why:
- Legal risk: False advertising laws (FTC, ASA, etc.)
- Consumer protection: Prevent fraud
- Platform policies: Ban on misleading ads

#### Examples:
- ❌ "Lose 30 lbs in 30 days guaranteed"
- ❌ "This supplement cures diabetes"
- ✅ "May help support healthy weight management" (with disclaimers)

---

### 8. Minors in Unsafe Contexts
**Status**: ❌ **BLOCKED**

#### Not Allowed:
- Children in dangerous situations
- Minors in adult contexts (alcohol, tobacco, dating)
- Exploitative depictions of children
- Targeting ads to children under 13 without COPPA compliance

#### Why:
- Legal risk: COPPA, child protection laws
- Ethical concerns: Protecting minors
- Platform policies: Strict rules on child safety

#### Examples:
- ❌ "Kid drinking energy drink"
- ❌ "Child alone near pool"
- ✅ "Family enjoying breakfast together" (with adults present)

---

## Safety Enforcement Layers

### Layer 1: Orchestrator Agent (Conversational Filter)
**When**: During user chat interaction  
**How**: Identifies unsafe requests in natural language

```
User: "Create an ad with someone firing a gun"
Orchestrator: "I can't create content with weapons or violence. 
              However, I can create an action-packed ad with 
              dynamic motion and energy. Would that work?"
```

**Actions**:
- Reject unsafe requests immediately
- Offer safe alternatives
- Educate user on why content was blocked

---

### Layer 2: Safety Validation Agent (Pre-Generation Check)
**When**: Before sending prompts to Sora  
**How**: Analyzes script + scene descriptions for violations

```json
{
  "status": "blocked",
  "violations": [
    {
      "category": "violence",
      "severity": "high",
      "scene": 3,
      "description": "Scene contains weapon reference"
    }
  ],
  "safe_alternative": {
    "scene_3_rewritten": "Person holding sports equipment instead of weapon"
  }
}
```

**Actions**:
- Block generation if violations detected
- Automatically rewrite prompts if fixable
- Log violations for audit

---

### Layer 3: Prompt Synthesis (Negative Prompts)
**When**: Generating Sora prompts  
**How**: Add comprehensive negative prompts

```
negative_prompt: "realistic violence, gore, blood, weapons, guns, knives,
                  nudity, sexual content, drugs, smoking, alcohol, 
                  hate symbols, real people likenesses, copyrighted characters,
                  trademarked brands, low quality, text overlay"
```

---

### Layer 4: Post-Generation Review (Future)
**When**: After video generated  
**How**: Computer vision analysis of output

**Planned Features**:
- Detect faces and check against known celebrities
- Identify logos/brands in background
- Flag unexpected unsafe content
- Allow human review before publish

---

## Brand Compliance Requirements

### 1. Brand Asset Usage
**Rules**:
- Only use brand assets uploaded by the user
- Never hallucinate competitor brands
- Logo placement only where user specifies
- Respect brand guidelines (colors, fonts, tone)

**Validation**:
- Ensure all products match uploaded reference images
- Verify color palette stays within brand colors
- Check logo appears at specified timestamp (e.g., final scene only)

---

### 2. Brand Tone & Voice
**Rules**:
- Match tone specified in Creative Bible (e.g., "premium", "playful", "professional")
- Avoid tone mismatches (e.g., comedy for luxury brand)
- Respect brand personality

**Examples**:
- Luxury brand: Minimalist, elegant, slow motion, soft lighting
- Energy drink: Fast cuts, vibrant colors, high energy, extreme sports
- B2B SaaS: Professional, clean, modern, office settings

---

### 3. Product Accuracy
**Rules**:
- Product appearance must match reference images
- No shape-shifting or inconsistent product design
- Maintain product scale and proportions
- Show product prominently (unless brand requests subtlety)

---

## Legal & Regulatory Compliance

### 1. Advertising Standards
**Requirements**:
- FTC (US): Disclose sponsored content, no deceptive claims
- ASA (UK): No misleading ads, substantiate claims
- GDPR (EU): No personal data misuse
- Platform-specific: Meta, TikTok, LinkedIn ad policies

**Enforcement**:
- Warn users about claim substantiation
- Require disclaimers for testimonials
- Flag financial/health products for extra review

---

### 2. Industry-Specific Rules

#### Financial Services
- Must include disclaimers ("Investing involves risk")
- No guaranteed return promises
- Comply with SEC/FINRA rules

#### Healthcare & Supplements
- No medical claims without FDA approval
- Include "These statements not evaluated by FDA" disclaimer
- No before/after images without disclosures

#### Alcohol & Tobacco
- Age-gate requirements (21+ in US, 18+ in EU)
- "Drink responsibly" messaging
- No targeting minors

#### Gambling
- Only in legal jurisdictions
- "Gamble responsibly" messaging
- Problem gambling helpline

---

## User Consequences for Violations

### Strike System

#### 1st Violation (Warning)
- Warning message in chat
- Generation blocked
- Offer safe alternatives
- Log incident

#### 2nd Violation (Soft Block)
- 24-hour generation cooldown
- Email notification explaining policies
- Require acknowledgment of terms

#### 3rd Violation (Account Review)
- Account suspended pending review
- Manual review by safety team
- Potential permanent ban

#### Severe Violations (Immediate Ban)
- Child exploitation content
- Terrorism or extremism
- Illegal activity
- Repeated intentional violations

---

## Reporting & Moderation

### User Reporting
- "Report this video" button
- Report categories: inappropriate, copyright, spam, other
- Review within 24 hours

### Automated Monitoring
- Scan all generated videos for safety violations
- Flag high-risk content for human review
- Track repeat offenders

### Transparency
- Public safety report (quarterly)
- Number of generations blocked
- Most common violation categories
- Policy updates

---

## Edge Cases & Nuance

### Contextual Exceptions

#### Alcohol in Background
- ❌ Person drinking alcohol
- ✅ Wine bottle on dinner table (background, not focus)
- ✅ Bar setting (if brand is restaurant/hospitality)

#### Swimwear
- ❌ Bikini model holding unrelated product
- ✅ Swimwear brand showing their own product
- ✅ Beach scene where swimwear is contextual

#### Competitive References
- ❌ Showing competitor logo/product
- ✅ Generic "leading brand" comparison (no logos)
- ✅ "Better than traditional options" (no specific competitor named)

---

## Safety Agent System Prompt

### Master Safety Prompt
```
You are the Safety Validation Agent for Zapcut.

Your job is to scan all scripts, scene descriptions, and prompts for:
1. Prohibited content (violence, nudity, drugs, hate, deepfakes, copyright)
2. Brand compliance violations
3. Legal/regulatory issues
4. Misleading claims

If ANY violation exists:
- Output "status": "blocked"
- List all violations with severity (low, medium, high, critical)
- Provide safe rewrite alternatives when possible

If content is safe:
- Output "status": "approved"
- Add comprehensive negative_prompt for generation

Never allow:
- Real people likenesses
- Copyrighted characters
- Competitor brands
- Unsafe behavior
- Misleading claims

Always enforce:
- Brand-safe content
- Synthetic humans only
- Royalty-free assets
```

---

## Updates & Changes

### Version History
- **v1.0** (Nov 15, 2025): Initial policy
- **v1.1** (TBD): Add post-generation CV detection
- **v2.0** (TBD): Industry-specific policy templates

### Policy Updates
- Reviewed quarterly
- User notification 30 days before enforcement
- Grandfather clause for existing content (case-by-case)

---

**Last Updated**: November 15, 2025  
**Policy Version**: 1.0  
**Next Review**: February 15, 2026  
**Contact**: safety@zapcut.video

