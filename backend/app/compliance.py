# Add this method to your ComplianceEngine class if not already present
def run_all_tests(self) -> List[ComplianceTestResult]:
    """Run all compliance tests and return results"""
    results = []
    
    # Eligibility Tests
    results.append(self.test_minimum_age())
    results.append(self.test_service_requirement())
    
    # Contribution Limit Tests
    results.append(self.test_annual_compensation_limit())
    results.append(self.test_deferral_limits())
    results.append(self.test_catch_up_limits())
    
    # Nondiscrimination Tests
    results.append(self.test_adp())
    results.append(self.test_acp())
    results.append(self.test_top_heavy())
    
    # Coverage Tests
    results.append(self.test_coverage_ratio())
    results.append(self.test_minimum_participation())
    
    return results