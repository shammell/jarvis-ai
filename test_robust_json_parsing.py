#!/usr/bin/env python3
"""
Test script for Robust JSON Parsing (Fix 12)
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_robust_json_parsing():
    """Test robust JSON parsing functionality"""
    logger.info("🧪 Testing Robust JSON Parsing (Fix 12)")
    logger.info("=" * 60)

    try:
        from core.system2_thinking import System2Thinking

        # Initialize without Groq client for testing
        system2 = System2Thinking(groq_api_key=None)

        # Test different response formats that might come from LLM
        test_cases = [
            # Strategy 1: JSON patterns
            ('{"score": 0.85}', 0.85),
            ('{"value": 0.9}', 0.9),
            ('{"result": 0.75}', 0.75),
            ('Score: {"score": 0.8}', 0.8),

            # Strategy 2: Numeric patterns
            ('score: 0.85', 0.85),
            ('Score is 0.75', 0.75),
            ('0.9', 0.9),
            ('The score is 0.6', 0.6),

            # Strategy 3: Percentage patterns
            ('85%', 0.85),
            ('Score: 90%', 0.9),
            ('75 percent', 0.75),

            # Strategy 4: Fraction patterns
            ('4/5', 0.8),
            ('3/4', 0.75),
            ('7/10', 0.7),

            # Strategy 5: Word-based scores
            ('excellent', 1.0),
            ('very good', 0.9),
            ('good', 0.8),
            ('average', 0.6),
            ('poor', 0.3),
            ('terrible', 0.1),

            # Strategy 6: Edge cases
            ('The answer is 85 out of 100', 0.85),
            ('Score between 0 and 100: 90', 0.9),
            ('0.85 is the final score', 0.85),

            # Error cases
            ('', 0.5),  # Empty
            ('not a number', 0.5),  # Invalid
            ('abc123', 0.5),  # Invalid
        ]

        logger.info(f"\n🧪 Testing {len(test_cases)} different response formats...")

        passed = 0
        failed = 0

        for i, (response_text, expected) in enumerate(test_cases, 1):
            try:
                result = system2._extract_score_robust(response_text)

                # Allow small tolerance for floating point comparison
                if abs(result - expected) < 0.01:
                    logger.info(f"✅ Test {i:2d}: '{response_text}' -> {result} (expected: {expected})")
                    passed += 1
                else:
                    logger.error(f"❌ Test {i:2d}: '{response_text}' -> {result} (expected: {expected})")
                    failed += 1

            except Exception as e:
                logger.error(f"❌ Test {i:2d}: '{response_text}' -> ERROR: {e}")
                failed += 1

        logger.info(f"\n📊 Results: {passed} passed, {failed} failed")

        if failed == 0:
            logger.info("\n" + "=" * 60)
            logger.info("✅ Robust JSON Parsing - ALL TESTS PASSED!")
            logger.info("   - JSON pattern parsing")
            logger.info("   - Numeric pattern parsing")
            logger.info("   - Percentage conversion")
            logger.info("   - Fraction parsing")
            logger.info("   - Word-based score mapping")
            logger.info("   - Error handling and fallbacks")
            return True
        else:
            logger.error(f"\n❌ {failed} tests failed")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_robust_json_parsing()
    sys.exit(0 if success else 1)