# Reasoning

Healf-Max treats recommendations as customer-confidence decisions. A customer asking for more energy is not always asking for a supplement; they may need a biomarker follow-up, a simpler routine, a product category comparison, or permission not to copy a protocol they saw online. The system therefore separates evidence, product fit, customer state, customer posture, editorial signals and trust signals so that the final answer can be grounded, safe, commercially useful and tonally native.

## 1. Decision Assistant, Not Supplement Recommender

The product is modelled around the next useful wellbeing decision. That keeps it closer to how a strong D2C wellness assistant should behave: clear, low-chaos, commercially aware, but not pushy. If the customer asks for energy, the assistant first asks what kind of energy problem this is: training load, sleep pressure, under-fuelling, biomarker follow-up, routine complexity, or category fit.

This prevents the weak version of the product: a generic supplement recommender that turns every concern into a stack.

## 2. Separated KB Signals

The KB keeps evidence, biomarkers, products, editorial signals, trust signals, tone patterns and moments separate because they do different jobs.

Evidence constrains claims. Biomarkers constrain routing. Product records explain category fit. Editorial and social-native tone reduce customer confusion. Trust records prevent false precision. Moments connect these signals into real customer situations such as Hyrox fatigue, low deep sleep and low ferritin.

## 3. Biomarkers Are Routing Constraints

Abnormal biomarkers should not trigger product recommendations. Low ferritin, high HbA1c, thyroid flags or medication context need careful follow-up language before commercial suggestions. In this build, the deterministic safety classifier catches those boundaries before the model speaks.

## 4. Category-First Product Fit

The assistant defaults to categories because product-level confidence is easy to overstate. Electrolytes, protein and magnesium can be useful lanes for a training and recovery moment, but the assistant should not pretend that a product treats fatigue, insomnia, anaemia or deficiency.

Product specificity can be added later when the KB has richer product records, contraindication metadata, evidence mapping and live availability.

## 5. Tone And Safety

The tone should feel native to a modern UK wellness brand: direct, warm, specific and occasionally cheeky around overwhelm. It should become plain and careful around pregnancy, medication, urgent symptoms, abnormal biomarkers or diagnosis requests.

Useful phrases include:

- not a bigger-stack moment
- start with the bottleneck
- boring wins
- not something to wellness your way around
- let the data be useful without letting it become your personality

## 6. Deliberately Out Of Scope

This first build does not include:

- live Healf inventory
- clinical interpretation
- dosing protocols
- account authentication
- hosted vector databases
- LangChain or LlamaIndex
- web UI polish
- autonomous agent execution
- medical-device style audit trails

Those can be added only when the data contracts and safety requirements justify them.

## 7. Genuine Uncertainty

The unresolved question is where the commercial threshold should sit for product-level specificity. A category-first answer is safer and more trustworthy for a take-home build. A production Healf version would need richer product metadata, supply constraints, practitioner-reviewed exclusions and measured conversion impact before becoming more product-specific.
