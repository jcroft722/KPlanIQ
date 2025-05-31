export interface ComplianceTestRun {
  id: number;
  file_id: number;
  file_name: string;
  run_date: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  results: any[];
} 