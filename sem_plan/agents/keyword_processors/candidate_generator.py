from __future__ import annotations

from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

from ...core.types import RawKeyword


class CandidateGenerator:
    """Generates additional candidate keywords using statistical and semantic methods."""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_candidates(self, existing_keywords: List[RawKeyword]) -> List[RawKeyword]:
        """Generate additional candidate keywords."""
        candidates = []
        
        # Get all text for analysis
        all_text = ' '.join([kw.keyword for kw in existing_keywords])
        
        # Statistical extraction
        candidates.extend(self._extract_ngrams(all_text))
        
        # TF-IDF analysis
        candidates.extend(self._extract_tfidf_keywords(existing_keywords))
        
        # Semantic grouping
        candidates.extend(self._extract_semantic_keywords(existing_keywords))
        
        return candidates
    
    def _extract_ngrams(self, text: str) -> List[RawKeyword]:
        """Extract n-grams from text."""
        candidates = []
        
        words = text.split()
        
        # Generate unigrams, bigrams, trigrams
        for n in range(1, 4):
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i+n])
                if len(ngram) > 3 and len(ngram.split()) == n:
                    candidates.append(RawKeyword(
                        keyword=ngram,
                        source="ngram_extraction"
                    ))
        
        return candidates
    
    def _extract_tfidf_keywords(self, keywords: List[RawKeyword]) -> List[RawKeyword]:
        """Extract keywords using TF-IDF analysis."""
        candidates = []
        
        try:
            # Create corpus
            corpus = [kw.keyword for kw in keywords if len(kw.keyword.split()) >= 2]
            
            if len(corpus) < 5:
                return candidates
            
            # TF-IDF vectorization
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=100,
                stop_words='english'
            )
            
            tfidf_matrix = vectorizer.fit_transform(corpus)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get top features
            tfidf_sums = tfidf_matrix.sum(axis=0).A1
            top_indices = tfidf_sums.argsort()[-20:]  # Top 20
            
            for idx in top_indices:
                feature = feature_names[idx]
                if len(feature.split()) >= 2:
                    candidates.append(RawKeyword(
                        keyword=feature,
                        source="tfidf_analysis"
                    ))
                    
        except Exception as e:
            print(f"TF-IDF extraction failed: {e}")
        
        return candidates
    
    def _extract_semantic_keywords(self, keywords: List[RawKeyword]) -> List[RawKeyword]:
        """Extract keywords using semantic clustering."""
        candidates = []
        
        try:
            # Get embeddings for existing keywords
            texts = [kw.keyword for kw in keywords if len(kw.keyword.split()) >= 2]
            
            if len(texts) < 10:
                return candidates
            
            embeddings = self.embedding_model.encode(texts)
            
            # Cluster similar keywords
            n_clusters = min(5, len(texts) // 2)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(embeddings)
            
            # Find cluster centers and similar keywords
            for cluster_id in range(n_clusters):
                cluster_keywords = [texts[i] for i, c in enumerate(clusters) if c == cluster_id]
                if cluster_keywords:
                    # Use the most representative keyword from each cluster
                    center_embedding = kmeans.cluster_centers_[cluster_id]
                    similarities = cosine_similarity([center_embedding], embeddings)[0]
                    
                    # Find keywords in this cluster
                    cluster_indices = [i for i, c in enumerate(clusters) if c == cluster_id]
                    cluster_similarities = [similarities[i] for i in cluster_indices]
                    
                    if cluster_similarities:
                        best_idx = cluster_indices[np.argmax(cluster_similarities)]
                        best_keyword = texts[best_idx]
                        
                        candidates.append(RawKeyword(
                            keyword=best_keyword,
                            source="semantic_clustering"
                        ))
                        
        except Exception as e:
            print(f"Semantic clustering failed: {e}")
        
        return candidates
