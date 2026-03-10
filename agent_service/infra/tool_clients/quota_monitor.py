"""API quota monitoring for auto show demo."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class QuotaInfo:
    """API quota information."""
    provider_name: str
    total_quota: int  # Total daily quota
    used_count: int  # Used count today
    remaining: int  # Remaining quota
    reset_time: float  # Unix timestamp when quota resets
    warning_threshold: int  # Warn when remaining < threshold
    
    @property
    def usage_rate(self) -> float:
        """Calculate usage rate."""
        if self.total_quota == 0:
            return 0.0
        return self.used_count / self.total_quota
    
    @property
    def is_warning(self) -> bool:
        """Check if should warn."""
        return self.remaining < self.warning_threshold
    
    @property
    def is_critical(self) -> bool:
        """Check if critical (< 10% remaining)."""
        return self.remaining < self.total_quota * 0.1


class QuotaMonitor:
    """Monitor API quota usage for demo."""
    
    def __init__(self):
        self._quotas: Dict[str, QuotaInfo] = {}
        self._init_quotas()
    
    def _init_quotas(self) -> None:
        """Initialize quota information."""
        # Baidu AI Search: 100 calls/day
        self._quotas["baidu_ai_search"] = QuotaInfo(
            provider_name="baidu_ai_search",
            total_quota=100,
            used_count=0,
            remaining=100,
            reset_time=self._get_next_reset_time(),
            warning_threshold=20,  # Warn at 20 remaining
        )
        
        # Baidu Search: 1000 calls/day (example)
        self._quotas["baidu_search"] = QuotaInfo(
            provider_name="baidu_search",
            total_quota=1000,
            used_count=0,
            remaining=1000,
            reset_time=self._get_next_reset_time(),
            warning_threshold=100,
        )
        
        # Tavily: 1000 calls/month (example)
        self._quotas["tavily"] = QuotaInfo(
            provider_name="tavily",
            total_quota=1000,
            used_count=0,
            remaining=1000,
            reset_time=self._get_next_reset_time(),
            warning_threshold=100,
        )
    
    def _get_next_reset_time(self) -> float:
        """Get next quota reset time (next day 00:00)."""
        import datetime
        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        reset = datetime.datetime.combine(tomorrow.date(), datetime.time.min)
        return reset.timestamp()
    
    def record_usage(self, provider_name: str) -> None:
        """Record API usage."""
        if provider_name in self._quotas:
            quota = self._quotas[provider_name]
            quota.used_count += 1
            quota.remaining = max(0, quota.total_quota - quota.used_count)
    
    def get_quota(self, provider_name: str) -> QuotaInfo | None:
        """Get quota info for provider."""
        return self._quotas.get(provider_name)
    
    def get_all_quotas(self) -> Dict[str, QuotaInfo]:
        """Get all quota information."""
        return self._quotas.copy()
    
    def check_warnings(self) -> list[str]:
        """Check for quota warnings.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        for provider, quota in self._quotas.items():
            if quota.is_critical:
                warnings.append(
                    f"🚨 CRITICAL: {provider} quota critical! "
                    f"Only {quota.remaining}/{quota.total_quota} remaining "
                    f"({quota.usage_rate:.1%} used)"
                )
            elif quota.is_warning:
                warnings.append(
                    f"⚠️  WARNING: {provider} quota low! "
                    f"{quota.remaining}/{quota.total_quota} remaining "
                    f"({quota.usage_rate:.1%} used)"
                )
        
        return warnings
    
    def reset_if_needed(self) -> None:
        """Reset quotas if reset time has passed."""
        now = time.time()
        
        for quota in self._quotas.values():
            if now >= quota.reset_time:
                quota.used_count = 0
                quota.remaining = quota.total_quota
                quota.reset_time = self._get_next_reset_time()
    
    def get_status_report(self) -> str:
        """Get formatted status report."""
        self.reset_if_needed()
        
        lines = ["=== API Quota Status ==="]
        
        for provider, quota in self._quotas.items():
            status = "🟢"
            if quota.is_critical:
                status = "🔴"
            elif quota.is_warning:
                status = "🟡"
            
            lines.append(
                f"{status} {provider}: {quota.remaining}/{quota.total_quota} "
                f"({quota.usage_rate:.1%} used)"
            )
        
        warnings = self.check_warnings()
        if warnings:
            lines.append("\n⚠️  Warnings:")
            lines.extend(f"  - {w}" for w in warnings)
        
        return "\n".join(lines)
