"""
Multi-Provider LLM System

Provides a clean abstraction for LLM providers with automatic fallback.
Supports: Groq, OpenRouter, HuggingFace Inference API

Usage:
    providers = ProviderFactory.create_provider_chain()
    provider = ProviderFactory.select_provider_with_preflight(providers)
    brain = Brain(provider=provider)
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import os
from openai import OpenAI  # Used by OpenRouter for API compatibility, NOT for OpenAI service
from groq import Groq


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured (has API key)"""
        pass
    
    @abstractmethod
    def preflight_check(self) -> bool:
        """Quick test to verify provider is working (< 5s)"""
        pass
    
    @abstractmethod
    def query(self, prompt: str, temperature: float = 0.3) -> str:
        """Send prompt and return response"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return model identifier for logging"""
        pass


class GroqProvider(LLMProvider):
    """Groq API provider (fast, free tier available)"""
    
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.model = model
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
    
    def name(self) -> str:
        return "Groq"
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def preflight_check(self) -> bool:
        """Test with minimal prompt to verify API is working"""
        if not self.is_available():
            print(f"  ❌ Groq not configured (missing GROQ_API_KEY)")
            return False
        
        try:
            response = self.query("Say 'OK'", temperature=0)
            return "ok" in response.lower()
        except Exception as e:
            error_msg = str(e).lower()
            
            # Categorize errors for better debugging
            if "invalid_api_key" in error_msg or "401" in error_msg:
                print(f"  ❌ INVALID API KEY - Check GROQ_API_KEY in .env")
            elif "rate_limit" in error_msg or "429" in error_msg:
                print(f"  ⚠️  Rate limited - Will try next provider")
            elif "timeout" in error_msg or "connection" in error_msg:
                print(f"  ⚠️  Network error - Will try next provider")
            else:
                print(f"  ⚠️  Groq preflight failed: {e}")
            
            return False
    
    def query(self, prompt: str, temperature: float = 0.3) -> str:
        if not self.client:
            raise RuntimeError("Groq client not initialized")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return response.choices[0].message.content
    
    def get_model_name(self) -> str:
        return f"groq:{self.model}"


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider (unified LLM access)"""
    
    def __init__(self, model: str = "meta-llama/llama-3.3-70b-instruct"):
        self.model = model
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            self.client = None
        else:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
    
    def name(self) -> str:
        return "OpenRouter"
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def preflight_check(self) -> bool:
        """Test with minimal prompt to verify API is working"""
        if not self.is_available():
            print(f"  ❌ OpenRouter not configured (missing OPENROUTER_API_KEY)")
            return False
        
        try:
            response = self.query("Say 'OK'", temperature=0)
            return "ok" in response.lower()
        except Exception as e:
            error_msg = str(e).lower()
            
            # Categorize errors for better debugging
            if "invalid_api_key" in error_msg or "401" in error_msg:
                print(f"  ❌ INVALID API KEY - Check OPENROUTER_API_KEY in .env")
            elif "rate_limit" in error_msg or "429" in error_msg:
                print(f"  ⚠️  Rate limited - Will try next provider")
            elif "timeout" in error_msg or "connection" in error_msg:
                print(f"  ⚠️  Network error - Will try next provider")
            else:
                print(f"  ⚠️  OpenRouter preflight failed: {e}")
            
            return False
    
    def query(self, prompt: str, temperature: float = 0.3) -> str:
        if not self.client:
            raise RuntimeError("OpenRouter client not initialized")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            extra_headers={
                "HTTP-Referer": "https://gist-ai.com",
                "X-Title": "Gist AI"
            }
        )
        return response.choices[0].message.content
    
    def get_model_name(self) -> str:
        return f"openrouter:{self.model}"


class ProviderFactory:
    """Creates and manages provider fallback chain"""
    
    @staticmethod
    def create_provider_chain() -> List[LLMProvider]:
        """
        Create provider chain dynamically based on available API keys.
        
        Priority order (first available wins):
        1. OpenRouter (primary - best reliability)
        2. Groq (fallback - fast but rate limited)
        
        Returns:
            List of available providers in priority order
        
        Raises:
            RuntimeError: If NO providers are configured
        """
        providers = []
        
        # Check OpenRouter (PRIMARY)
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            print("  ✓ OpenRouter configured (primary)")
            providers.append(OpenRouterProvider())
        else:
            print("  ⚠️  OpenRouter not configured (missing OPENROUTER_API_KEY)")
        
        # Check Groq (OPTIONAL FALLBACK)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            print("  ✓ Groq configured (fallback)")
            providers.append(GroqProvider())
        else:
            print("  ⚠️  Groq not configured (missing GROQ_API_KEY) - skipping")
        
        # Ensure at least one provider is available
        if not providers:
            raise RuntimeError(
                "❌ No LLM providers configured!\n"
                "   Please set at least one API key:\n"
                "   - OPENROUTER_API_KEY (primary)\n"
                "   - GROQ_API_KEY (optional fallback)"
            )
        
        print(f"  📋 Registered {len(providers)} provider(s): {', '.join(p.name() for p in providers)}")
        return providers
    
    @staticmethod
    def select_provider_with_preflight(providers: List[LLMProvider], skip_preflight: bool = False) -> LLMProvider:
        """
        Run preflight checks and return first working provider.
        
        Args:
            providers: List of providers to test (in priority order)
            skip_preflight: If True, skip preflight checks and use first available
        
        Returns:
            First working provider
        
        Raises:
            RuntimeError: If all providers fail preflight checks
        """
        if skip_preflight:
            # Use first available provider without testing
            for provider in providers:
                if provider.is_available():
                    print(f"  ⚡ Skipping preflight checks, using {provider.name()}")
                    return provider
            raise RuntimeError("No providers available")
        
        print("🔍 Running preflight checks...")
        failed_providers = []
        
        for provider in providers:
            # Skip providers that aren't configured (no API key)
            if not provider.is_available():
                print(f"  ⏭️  Skipping {provider.name()} (not configured)")
                continue
            
            print(f"  🧪 Testing {provider.name()}...")
            if provider.preflight_check():
                print(f"  ✅ {provider.name()} is working!")
                return provider
            else:
                failed_providers.append(provider.name())
        
        # All configured providers failed
        raise RuntimeError(
            f"❌ All configured providers failed preflight checks: {', '.join(failed_providers)}\n"
            f"   Please verify your API keys:\n"
            f"   - OPENROUTER_API_KEY\n"
            f"   - GROQ_API_KEY (fallback)"
        )
