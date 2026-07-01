# Reasoning

We want customers to be able to access the "Healf Intelligence Layer" using whatever tooling or connector that they use locally. From my perspective, it's as important to ensure the brand tone, customer profile, and product catalog are made readily available to the model vs. implementing some insanely in-depth feature set.

Healf's customers know Healf.
They know the tone.
They know what to expect.

The 4.8 star Trustpilot rating reaffirms this.
When communicating with the brand (agentically), they are not seeking some grand revelation, they are seeking consistency and reliability.

I focused the knowledge base on Healf's public presence exactly for this reason.
Website scrape, IG scrape, Facebook scrape, Trustpilot scrape, all fed into one "agent managed" knowledge base.

My work with knowledge bases has told me this. 
Don't overthink it.

It's for the model.
Leave it to the model. 

# Knowledge Structure
86 lightweight markdown files, Andrej Karpathy-inspired graph retrieval. 
Each of which address a key component of either Healf or a potential query, that the model can access quickly and reliably.

# Context Assembly
For each turn, I assemble the prompt around the smallest viable/useful context window. The model can match the prompt and keywords inside of it with the carefully selected information inside the knowledge base, and then formulate it's response accordingly - keeping it highly "aware" without the immediate requirement for web access.

# Safety model
Simple, yet firm safety boundary: wellness and product guidance is allowed, but you are not a doctor.
Risky cases, given access to biomarkers, can calmly be elevated to appropriate medical resources.
Naturally, not everything will be caught, especially in a prototype, but with a firm enough boundary and enough data - this can be refined, and the "failure rate" can be reduced significantly. 

# Out Of Scope

I chose not to include:

- live Healf inventory
- clinical interpretation (assistant does not provide medical advice or diagnose)
- dosing protocols and the like
- etc

It was more important to me that the tool served as a reasonably intelligent layer on top of what a customer can already see online.

What good is "advanced tooling" if it isn't aware of things a customer would be aware of?

# One Uncertain Decision
To lean fully in the direction of "this feels like you are speaking to someone at Healf" vs. having a rich medical research corpus with graceful degredation if a query touches a sensitive topic. To me, the brand has a sort of emotional/personal connection with the customers, and replacing this with a robotic chatbot who cannot hold the "feeling of the brand" felt like an expensive tradeoff. But again - uncertain, would leave this up to leadership to decide.

# Future State

Many cool directions we could take this.

"Claude, check on my Healf order."
"Chat, can you reorder my Magnesium from Healf?"
+ a myriad of other revenue generating natural language queries that are just waiting for us to build tooling around them.

- Charlie
