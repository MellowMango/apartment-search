"""
LabNameClassifier - ML-powered lab name detection from unstructured text.

This module implements a lightweight neural network classifier that can identify
laboratory names and research center names from unstructured text blocks on
faculty pages. Uses TF-IDF features and a small MLP for fast inference.
"""

import os
import json
import logging
import pickle
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from bs4 import BeautifulSoup
import joblib

logger = logging.getLogger(__name__)


class LabNameClassifier:
    """Lightweight ML classifier for detecting lab names in text."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the lab name classifier.
        
        Args:
            model_path: Path to saved model file. If None, uses default location.
        """
        self.model_path = model_path or "models/lab_classifier.pkl"
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2),  # Include bigrams for better context
            min_df=2,  # Ignore very rare terms
            max_df=0.8  # Ignore very common terms
        )
        self.model = MLPClassifier(
            hidden_layer_sizes=(10,),
            max_iter=500,
            random_state=42,
            alpha=0.01,  # L2 regularization
            early_stopping=True,
            validation_fraction=0.1
        )
        self.is_trained = False
        self.feature_names = []
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Try to load existing model
        if os.path.exists(self.model_path):
            self.load_model()
    
    def train(self, sentences: List[str], labels: List[bool], 
              test_size: float = 0.2, verbose: bool = True) -> Dict:
        """
        Train the classifier on labeled examples.
        
        Args:
            sentences: List of text sentences
            labels: List of boolean labels (True = lab name, False = other)
            test_size: Fraction of data to use for testing
            verbose: Whether to print training progress
            
        Returns:
            Dict with training metrics
        """
        if len(sentences) != len(labels):
            raise ValueError("Number of sentences must match number of labels")
            
        if len(sentences) < 20:
            logger.warning("Very small training set - consider collecting more data")
            
        logger.info(f"Training classifier with {len(sentences)} examples")
        
        # Split into train/test
        X_train, X_test, y_train, y_test = train_test_split(
            sentences, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        # Vectorize text
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Store feature names for analysis
        self.feature_names = self.vectorizer.get_feature_names_out()
        
        # Train model
        logger.info("Training neural network...")
        self.model.fit(X_train_vec, y_train)
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        
        metrics = {
            "accuracy": accuracy,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "positive_samples": sum(labels),
            "negative_samples": len(labels) - sum(labels)
        }
        
        if verbose:
            logger.info(f"Training completed - Accuracy: {accuracy:.3f}")
            print("\nClassification Report:")
            print(classification_report(y_test, y_pred, 
                                      target_names=['Not Lab', 'Lab Name']))
        
        self.is_trained = True
        return metrics
    
    def predict(self, sentence: str) -> Tuple[bool, float]:
        """
        Predict if a sentence contains a lab name.
        
        Args:
            sentence: Text to classify
            
        Returns:
            Tuple of (is_lab_name: bool, confidence: float)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first or load existing model.")
            
        # Vectorize input
        X = self.vectorizer.transform([sentence])
        
        # Get prediction and confidence
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        confidence = probabilities.max()
        
        return bool(prediction), float(confidence)
    
    def predict_batch(self, sentences: List[str]) -> List[Tuple[bool, float]]:
        """
        Predict for multiple sentences efficiently.
        
        Args:
            sentences: List of sentences to classify
            
        Returns:
            List of (is_lab_name, confidence) tuples
        """
        if not self.is_trained:
            raise ValueError("Model not trained.")
            
        # Vectorize all sentences at once
        X = self.vectorizer.transform(sentences)
        
        # Get predictions and probabilities
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        confidences = probabilities.max(axis=1)
        
        return [(bool(pred), float(conf)) for pred, conf in zip(predictions, confidences)]
    
    def scan_text_blocks(self, soup: BeautifulSoup, 
                        confidence_threshold: float = 0.7) -> List[Dict]:
        """
        Scan all text blocks in HTML for potential lab names.
        
        Args:
            soup: BeautifulSoup object to scan
            confidence_threshold: Minimum confidence for inclusion
            
        Returns:
            List of dicts with keys: text, confidence, tag, position
        """
        if not self.is_trained:
            logger.warning("Model not trained - returning empty results")
            return []
            
        candidates = []
        
        # Define tags that commonly contain lab names
        target_tags = ['p', 'div', 'li', 'td', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
        for i, tag in enumerate(soup.find_all(target_tags)):
            text = tag.get_text(strip=True)
            
            # Skip very short or very long text
            if len(text) < 10 or len(text) > 500:
                continue
                
            # Skip text that's obviously not a lab name
            if self._is_obviously_not_lab(text):
                continue
                
            # Classify the text
            is_lab_name, confidence = self.predict(text)
            
            if is_lab_name and confidence >= confidence_threshold:
                candidates.append({
                    "text": text,
                    "confidence": confidence,
                    "tag": tag.name,
                    "position": i,
                    "length": len(text)
                })
        
        # Sort by confidence descending
        return sorted(candidates, key=lambda x: x["confidence"], reverse=True)
    
    def _is_obviously_not_lab(self, text: str) -> bool:
        """Quick heuristic checks to filter out obvious non-lab text."""
        text_lower = text.lower()
        
        # Skip if it looks like navigation, contact info, etc.
        skip_patterns = [
            "email", "phone", "address", "contact", "copyright",
            "all rights reserved", "privacy policy", "terms of service",
            "home", "about", "news", "events", "calendar",
            "login", "register", "search", "menu", "navigation"
        ]
        
        for pattern in skip_patterns:
            if pattern in text_lower:
                return True
                
        # Skip if it's mostly numbers or special characters
        alpha_ratio = sum(c.isalpha() for c in text) / len(text)
        if alpha_ratio < 0.5:
            return True
            
        return False
    
    def get_feature_importance(self, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Get the most important features for classification.
        
        Args:
            top_n: Number of top features to return
            
        Returns:
            List of (feature_name, importance) tuples
        """
        if not self.is_trained or not hasattr(self.model, 'coefs_'):
            return []
            
        # Get weights from first layer
        weights = self.model.coefs_[0].mean(axis=1)  # Average across hidden units
        
        # Get feature names and sort by absolute weight
        feature_weights = list(zip(self.feature_names, np.abs(weights)))
        feature_weights.sort(key=lambda x: x[1], reverse=True)
        
        return feature_weights[:top_n]
    
    def save_model(self, path: Optional[str] = None) -> None:
        """Save the trained model and vectorizer."""
        save_path = path or self.model_path
        
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
            
        model_data = {
            'vectorizer': self.vectorizer,
            'model': self.model,
            'is_trained': self.is_trained,
            'feature_names': self.feature_names
        }
        
        with open(save_path, 'wb') as f:
            pickle.dump(model_data, f)
            
        logger.info(f"Model saved to {save_path}")
    
    def load_model(self, path: Optional[str] = None) -> bool:
        """
        Load a previously saved model.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        load_path = path or self.model_path
        
        try:
            with open(load_path, 'rb') as f:
                model_data = pickle.load(f)
                
            self.vectorizer = model_data['vectorizer']
            self.model = model_data['model']
            self.is_trained = model_data['is_trained']
            self.feature_names = model_data.get('feature_names', [])
            
            logger.info(f"Model loaded from {load_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load model from {load_path}: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """Get information about the current model."""
        info = {
            "is_trained": self.is_trained,
            "model_path": self.model_path,
            "vectorizer_features": len(self.feature_names) if self.feature_names else 0
        }
        
        if self.is_trained:
            info.update({
                "model_type": "MLPClassifier",
                "hidden_layers": self.model.hidden_layer_sizes,
                "n_features": self.vectorizer.max_features,
                "ngram_range": self.vectorizer.ngram_range
            })
            
        return info


def create_sample_training_data() -> Tuple[List[str], List[bool]]:
    """
    Create sample training data for development and testing.
    
    Returns:
        Tuple of (sentences, labels)
    """
    # Positive examples (lab names)
    positive_examples = [
        "Laboratory for Cognitive Neuroscience",
        "Advanced Materials Research Center",
        "Computational Biology Laboratory",
        "Human-Computer Interaction Lab",
        "Artificial Intelligence Research Group",
        "Behavioral Economics Laboratory",
        "Center for Machine Learning",
        "Quantum Computing Research Lab",
        "Social Psychology Research Center",
        "Biomedical Engineering Laboratory",
        "Data Science Research Group",
        "Robotics and Automation Lab",
        "Environmental Science Research Center",
        "Genomics Research Laboratory",
        "Digital Humanities Center",
        "Neural Engineering Laboratory",
        "Computer Vision Research Group",
        "Language Processing Lab",
        "Systems Biology Center",
        "Cybersecurity Research Laboratory",
        "Climate Change Research Institute",
        "Renewable Energy Laboratory",
        "Medical Imaging Research Center",
        "Bioinformatics Research Group",
        "Virtual Reality Laboratory"
    ]
    
    # Negative examples (not lab names)
    negative_examples = [
        "The professor teaches undergraduate courses in computer science",
        "Office hours are held on Tuesdays and Thursdays",
        "Students can access course materials online",
        "Research interests include machine learning and data mining",
        "Dr. Smith received her PhD from Stanford University",
        "Publications are available on the faculty website",
        "Contact information can be found in the directory",
        "The department offers both undergraduate and graduate programs",
        "Admission requirements vary by program level",
        "Faculty members collaborate with industry partners",
        "The university is located in downtown Phoenix",
        "Parking is available in the north parking structure",
        "The library is open 24 hours during finals week",
        "Tuition and fees information is available online",
        "Student services include career counseling and advising",
        "The campus bookstore sells textbooks and supplies",
        "Graduation ceremonies are held twice per year",
        "Financial aid is available for qualified students",
        "The dining hall serves meals from 7am to 9pm",
        "Dormitory rooms are furnished with basic amenities",
        "Athletic programs include basketball and soccer",
        "The health center provides medical services to students",
        "International students need to obtain a visa",
        "Registration for spring semester begins in November",
        "Academic calendar information is posted online"
    ]
    
    # Combine and create labels
    sentences = positive_examples + negative_examples
    labels = [True] * len(positive_examples) + [False] * len(negative_examples)
    
    return sentences, labels


def demo_lab_classifier():
    """Demo function to show LabNameClassifier in action."""
    print("Lab Name Classifier Demo")
    print("=" * 40)
    
    # Create and train classifier
    classifier = LabNameClassifier()
    
    # Get sample training data
    sentences, labels = create_sample_training_data()
    
    print(f"Training with {len(sentences)} examples...")
    metrics = classifier.train(sentences, labels, verbose=True)
    
    # Test on some examples
    test_sentences = [
        "Cognitive Science Research Laboratory",
        "The professor offers office hours",
        "Machine Learning and AI Center",
        "Students must register for courses",
        "Biomedical Engineering Research Group"
    ]
    
    print("\nTesting on examples:")
    for sentence in test_sentences:
        is_lab, confidence = classifier.predict(sentence)
        print(f"'{sentence[:50]}...' -> Lab: {is_lab}, Confidence: {confidence:.3f}")
    
    # Show feature importance
    print("\nTop important features:")
    for feature, importance in classifier.get_feature_importance(10):
        print(f"  {feature}: {importance:.3f}")
    
    # Save the model
    classifier.save_model()
    print(f"\nModel saved to {classifier.model_path}")


if __name__ == "__main__":
    demo_lab_classifier() 