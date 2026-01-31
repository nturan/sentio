"""
Rating pattern algorithms for generating realistic impulse histories.
"""

import math
import random
from typing import List, Dict, Literal

PatternType = Literal[
    "honeymoon_dip_recovery",
    "steady_improvement",
    "struggle_then_improve",
    "volatile",
    "declining"
]


class RatingPatternGenerator:
    """
    Generates rating patterns over time for stakeholder assessments.

    Simulates realistic change management dynamics where different
    stakeholder groups experience the change process differently.
    """

    # Base ratings for each stakeholder group type
    GROUP_BASELINES: Dict[str, float] = {
        "fuehrungskraefte": 6.5,  # Closer to management, more positive
        "multiplikatoren": 6.0,   # Balanced view
        "mitarbeitende": 5.5,     # Most skeptical initially
    }

    # Difficulty modifiers for indicators (applied to base rating)
    INDICATOR_MODIFIERS: Dict[str, float] = {
        # Core indicators
        "orientierung_sinn": 0.0,        # Communicated first, neutral
        "psychologische_sicherheit": -0.5,  # Takes time to build
        "empowerment": -0.3,             # Requires trust
        "partizipation": 0.0,            # Depends on effort
        "wertschaetzung": 0.2,           # Easier to demonstrate
        # Fuehrungskraefte indicators
        "ressourcenfreigabe": -0.4,      # Political, difficult
        "aktive_kommunikation": 0.1,     # Trainable
        "widerstandsmanagement": -0.5,   # Very challenging
        "vorbildfunktion": 0.3,          # Visible, easier to track
    }

    @classmethod
    def get_base_rating(cls, group_type: str, indicator_key: str) -> float:
        """Get the base rating for a group type and indicator."""
        base = cls.GROUP_BASELINES.get(group_type, 6.0)
        modifier = cls.INDICATOR_MODIFIERS.get(indicator_key, 0.0)
        return max(1.0, min(10.0, base + modifier))

    @classmethod
    def generate_pattern(
        cls,
        pattern_type: PatternType,
        num_points: int,
        group_type: str,
        indicator_key: str,
        noise_level: float = 0.3
    ) -> List[float]:
        """
        Generate a series of ratings following a specific pattern.

        Args:
            pattern_type: The type of pattern to generate
            num_points: Number of data points (impulses)
            group_type: Stakeholder group type for baseline
            indicator_key: Indicator key for modifier
            noise_level: Standard deviation of random noise (0-1)

        Returns:
            List of ratings (1-10 scale)
        """
        base = cls.get_base_rating(group_type, indicator_key)

        if pattern_type == "honeymoon_dip_recovery":
            values = cls._honeymoon_dip_recovery(num_points, base)
        elif pattern_type == "steady_improvement":
            values = cls._steady_improvement(num_points, base)
        elif pattern_type == "struggle_then_improve":
            values = cls._struggle_then_improve(num_points, base)
        elif pattern_type == "volatile":
            values = cls._volatile(num_points, base)
        elif pattern_type == "declining":
            values = cls._declining(num_points, base)
        else:
            # Default to steady
            values = [base] * num_points

        # Add noise and clamp
        noisy_values = []
        for v in values:
            noise = random.gauss(0, noise_level)
            clamped = max(1.0, min(10.0, v + noise))
            noisy_values.append(round(clamped, 1))

        return noisy_values

    @classmethod
    def _honeymoon_dip_recovery(cls, n: int, base: float) -> List[float]:
        """
        Pattern: High optimism -> reality check valley -> gradual recovery
        Typical for: Fuehrungskraefte who start enthusiastic then face implementation challenges

        Shape: 7.5 -> 5 (at ~40%) -> 6.5
        """
        values = []
        for i in range(n):
            progress = i / max(1, n - 1)  # 0 to 1

            if progress < 0.15:
                # Honeymoon phase: start high
                val = base + 1.5 - (progress / 0.15) * 0.5
            elif progress < 0.45:
                # Dip phase: dropping
                dip_progress = (progress - 0.15) / 0.30
                val = base + 1.0 - dip_progress * 2.5
            else:
                # Recovery phase: climbing back
                recovery_progress = (progress - 0.45) / 0.55
                val = base - 1.5 + recovery_progress * 2.0

            values.append(val)
        return values

    @classmethod
    def _steady_improvement(cls, n: int, base: float) -> List[float]:
        """
        Pattern: Gradual consistent improvement over time
        Typical for: Multiplikatoren who are committed and see gradual results

        Shape: base-0.5 -> base+1.5 (linear with slight curve)
        """
        values = []
        for i in range(n):
            progress = i / max(1, n - 1)
            # Slight S-curve for more natural progression
            curved = 0.5 * (1 + math.tanh((progress - 0.5) * 3))
            val = (base - 0.5) + curved * 2.0
            values.append(val)
        return values

    @classmethod
    def _struggle_then_improve(cls, n: int, base: float) -> List[float]:
        """
        Pattern: Low start -> extended struggle -> turning point -> rapid improvement
        Typical for: Mitarbeitende who need time to see benefits

        Shape: 4.5 -> flat at 5 (60%) -> 7
        """
        values = []
        for i in range(n):
            progress = i / max(1, n - 1)

            if progress < 0.6:
                # Struggle phase: low and flat with slight improvements
                val = base - 1.5 + progress * 0.5
            else:
                # Improvement phase: rapid climb
                improvement_progress = (progress - 0.6) / 0.4
                val = base - 1.0 + improvement_progress * 2.5

            values.append(val)
        return values

    @classmethod
    def _volatile(cls, n: int, base: float) -> List[float]:
        """
        Pattern: Oscillating up and down with no clear trend
        Typical for: Groups with inconsistent leadership or mixed signals

        Shape: Sine wave around base +/- 1.5
        """
        values = []
        for i in range(n):
            progress = i / max(1, n - 1)
            # Multiple sine waves for irregular pattern
            wave1 = math.sin(progress * 4 * math.pi) * 1.0
            wave2 = math.sin(progress * 2.5 * math.pi + 1) * 0.5
            val = base + wave1 + wave2
            values.append(val)
        return values

    @classmethod
    def _declining(cls, n: int, base: float) -> List[float]:
        """
        Pattern: Concerning downward trend
        Typical for: Crisis situations, leadership issues, loss of trust

        Shape: base+0.5 -> base-2.0 (gradual decline)
        """
        values = []
        for i in range(n):
            progress = i / max(1, n - 1)
            # Accelerating decline
            decline = progress * progress * 2.5
            val = base + 0.5 - decline
            values.append(val)
        return values

    @classmethod
    def generate_assessment_history(
        cls,
        pattern_type: PatternType,
        num_impulses: int,
        group_type: str,
        indicator_keys: List[str],
        noise_level: float = 0.3
    ) -> Dict[str, List[float]]:
        """
        Generate complete assessment history for a stakeholder group.

        Args:
            pattern_type: Base pattern for all indicators
            num_impulses: Number of assessment dates
            group_type: Stakeholder group type
            indicator_keys: List of indicator keys to generate
            noise_level: Noise level for variation

        Returns:
            Dict mapping indicator_key -> list of ratings over time
        """
        history = {}
        for key in indicator_keys:
            # Slightly vary noise per indicator for natural feel
            indicator_noise = noise_level + random.uniform(-0.1, 0.1)
            history[key] = cls.generate_pattern(
                pattern_type,
                num_impulses,
                group_type,
                key,
                max(0.1, indicator_noise)
            )
        return history
