"""Quick test for Transformer NLP"""
from transformer_nlp import get_nlp_analyzer

print("Loading DistilBERT model...")
analyzer = get_nlp_analyzer()
print("✓ Transformer loaded successfully\n")

text = "Estoy muy motivado para ser monitor de Cálculo I porque tengo excelentes calificaciones y me apasiona enseñar."
print(f"Analyzing: '{text[:50]}...'")

result = analyzer.analyze(text)
print(f"\n✓ Quality: {result['quality_label']}")
print(f"✓ Confidence: {result['confidence']:.1%}")
print(f"✓ Sentiment: {result['sentiment']}")
print(f"\nCourse compliance:")
print(f"  - Transformer architecture: {result['course_compliance']['model_type']}")
print(f"  - Attention heads: {result['course_compliance']['attention_heads']}")
print(f"  - Parameters: {result['course_compliance']['parameters']}")
