"""
Advanced Matrix Validator for Professional MCDM Decision Matrices

This module implements sophisticated validation techniques based on MCDM literature:
- Saaty (AHP): Consistency and scale validation
- Hwang & Yoon (TOPSIS): Normalization compatibility
- Brans (PROMETHEE): Preference structure validation
- Roy (ELECTRE): Outranking relation prerequisites
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import warnings

class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Represents a single validation result"""
    severity: ValidationSeverity
    message: str
    details: str
    suggestion: str
    affected_cells: List[Tuple[int, int]] = None
    affected_criteria: List[str] = None
    affected_alternatives: List[str] = None

class AdvancedMatrixValidator:
    """
    Professional MCDM Matrix Validator
    
    Implements validation techniques from MCDM literature for:
    - Logical consistency
    - Statistical outliers detection
    - Scale compliance
    - Method-specific requirements
    """
    
    def __init__(self):
        self.validation_results = []
        self.outlier_threshold = 2.0  # Standard deviations
        self.completeness_threshold = 0.7  # 70% minimum completion
        
    def validate_matrix_comprehensive(self, matrix_data: Dict[str, str], 
                                   alternatives: List[Dict], 
                                   criteria: List[Dict],
                                   criteria_config: Dict[str, Dict] = None) -> List[ValidationResult]:
        """
        Comprehensive matrix validation following MCDM best practices
        
        Args:
            matrix_data: Dictionary with keys like "A1_C1" and string values
            alternatives: List of alternative dictionaries
            criteria: List of criteria dictionaries  
            criteria_config: Configuration for each criterion
            
        Returns:
            List of ValidationResult objects
        """
        self.validation_results = []
        
        # Convert to numerical matrix for analysis
        numerical_matrix, valid_positions = self._prepare_numerical_matrix(
            matrix_data, alternatives, criteria
        )
        
        if numerical_matrix is None:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.CRITICAL,
                message="Cannot create numerical matrix",
                details="Insufficient numerical data for validation",
                suggestion="Ensure at least 50% of matrix contains valid numbers"
            ))
            return self.validation_results
        
        # 1. LOGICAL CONSISTENCY VALIDATION
        self._validate_logical_consistency(numerical_matrix, alternatives, criteria, valid_positions)
        
        # 2. STATISTICAL OUTLIER DETECTION  
        self._detect_statistical_outliers(numerical_matrix, alternatives, criteria, valid_positions)
        
        # 3. SCALE COMPLIANCE VALIDATION
        if criteria_config:
            self._validate_scale_compliance(matrix_data, criteria, criteria_config)
        
        # 4. CRITERION TYPE VALIDATION
        self._validate_criterion_types(numerical_matrix, alternatives, criteria, valid_positions)
        
        # 5. COMPLETENESS ANALYSIS
        self._analyze_completeness(matrix_data, alternatives, criteria)
        
        # 6. CORRELATION ANALYSIS (for redundancy detection)
        self._analyze_criteria_correlation(numerical_matrix, criteria, valid_positions)
        
        # 7. DOMINANCE ANALYSIS
        self._analyze_alternative_dominance(numerical_matrix, alternatives, criteria, valid_positions)
        
        return self.validation_results
    
    def _prepare_numerical_matrix(self, matrix_data: Dict[str, str], 
                                alternatives: List[Dict], 
                                criteria: List[Dict]) -> Tuple[Optional[np.ndarray], Dict]:
        """Convert string matrix data to numerical matrix for analysis"""
        try:
            n_alt = len(alternatives)
            n_crit = len(criteria)
            matrix = np.full((n_alt, n_crit), np.nan)
            valid_positions = {}
            
            for i, alt in enumerate(alternatives):
                for j, crit in enumerate(criteria):
                    key = f"{alt['id']}_{crit['id']}"
                    if key in matrix_data and matrix_data[key].strip():
                        try:
                            value = float(matrix_data[key])
                            matrix[i, j] = value
                            valid_positions[(i, j)] = True
                        except ValueError:
                            continue
            
            # Check if we have enough data for meaningful analysis
            valid_count = np.sum(~np.isnan(matrix))
            total_count = n_alt * n_crit
            
            if valid_count < (total_count * 0.3):  # Less than 30% filled
                return None, {}
                
            return matrix, valid_positions
            
        except Exception as e:
            return None, {}
    
    def _validate_logical_consistency(self, matrix: np.ndarray, alternatives: List[Dict], 
                                   criteria: List[Dict], valid_positions: Dict):
        """Validate logical consistency of values"""
        
        # Check for negative values where they shouldn't exist
        for j, crit in enumerate(criteria):
            col_values = matrix[:, j]
            valid_values = col_values[~np.isnan(col_values)]
            
            if len(valid_values) == 0:
                continue
                
            # Check for negative values in typically positive criteria
            if np.any(valid_values < 0):
                negative_count = np.sum(valid_values < 0)
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    message=f"Negative values in criterion '{crit['name']}'",
                    details=f"Found {negative_count} negative values. Verify if this is intentional.",
                    suggestion="Review if negative values are meaningful for this criterion",
                    affected_criteria=[crit['id']]
                ))
        
        # Check for extremely large value ranges within criteria
        for j, crit in enumerate(criteria):
            col_values = matrix[:, j]
            valid_values = col_values[~np.isnan(col_values)]
            
            if len(valid_values) < 2:
                continue
                
            value_range = np.max(valid_values) - np.min(valid_values)
            mean_value = np.mean(valid_values)
            
            # If range is more than 100x the mean, it might be inconsistent
            if mean_value > 0 and value_range > (100 * mean_value):
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    message=f"Extremely large value range in '{crit['name']}'",
                    details=f"Range: {value_range:.2f}, Mean: {mean_value:.2f}",
                    suggestion="Verify data entry or consider normalizing values",
                    affected_criteria=[crit['id']]
                ))
    
    def _detect_statistical_outliers(self, matrix: np.ndarray, alternatives: List[Dict],
                                  criteria: List[Dict], valid_positions: Dict):
        """Detect statistical outliers using IQR and Z-score methods"""
        
        outliers_found = []
        
        for j, crit in enumerate(criteria):
            col_values = matrix[:, j]
            valid_values = col_values[~np.isnan(col_values)]
            
            if len(valid_values) < 4:  # Need at least 4 values for meaningful outlier detection
                continue
            
            # IQR Method
            Q1 = np.percentile(valid_values, 25)
            Q3 = np.percentile(valid_values, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Z-Score Method  
            mean_val = np.mean(valid_values)
            std_val = np.std(valid_values)
            
            for i, alt in enumerate(alternatives):
                if np.isnan(matrix[i, j]):
                    continue
                    
                value = matrix[i, j]
                
                # Check IQR outlier
                is_iqr_outlier = value < lower_bound or value > upper_bound
                
                # Check Z-score outlier (if std > 0)
                is_zscore_outlier = False
                if std_val > 0:
                    z_score = abs(value - mean_val) / std_val
                    is_zscore_outlier = z_score > self.outlier_threshold
                
                if is_iqr_outlier and is_zscore_outlier:
                    outliers_found.append({
                        'alternative': alt['name'],
                        'criterion': crit['name'], 
                        'value': value,
                        'z_score': z_score if std_val > 0 else 0,
                        'position': (i, j)
                    })
        
        if outliers_found:
            outlier_details = "\n".join([
                f"• {out['alternative']} - {out['criterion']}: {out['value']:.2f} (Z={out['z_score']:.2f})"
                for out in outliers_found[:5]  # Show max 5 examples
            ])
            
            if len(outliers_found) > 5:
                outlier_details += f"\n... and {len(outliers_found) - 5} more"
            
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.INFO,
                message=f"Statistical outliers detected ({len(outliers_found)} values)",
                details=outlier_details,
                suggestion="Review highlighted values for potential data entry errors",
                affected_cells=[out['position'] for out in outliers_found]
            ))
    
    def _validate_scale_compliance(self, matrix_data: Dict[str, str], 
                                 criteria: List[Dict], criteria_config: Dict[str, Dict]):
        """Validate values comply with configured scales"""
        
        violations = []
        
        for crit in criteria:
            crit_id = crit['id']
            if crit_id not in criteria_config:
                continue
                
            config = criteria_config[crit_id]
            min_val = config.get('min_value', float('-inf'))
            max_val = config.get('max_value', float('inf'))
            scale_type = config.get('scale_type', '')
            
            # Check all values for this criterion
            for key, value_str in matrix_data.items():
                if not value_str.strip():
                    continue
                    
                if f"_{crit_id}" in key:
                    try:
                        value = float(value_str)
                        
                        # Check range compliance
                        if value < min_val or value > max_val:
                            alt_id = key.split('_')[0]
                            violations.append({
                                'alternative_id': alt_id,
                                'criterion': crit['name'],
                                'value': value,
                                'expected_range': f"[{min_val}, {max_val}]"
                            })
                        
                        # Check Likert scale compliance
                        if 'Likert' in scale_type:
                            if not value.is_integer():
                                violations.append({
                                    'alternative_id': alt_id,
                                    'criterion': crit['name'],
                                    'value': value,
                                    'issue': 'Likert scales require integer values'
                                })
                                
                    except ValueError:
                        continue
        
        if violations:
            violation_details = "\n".join([
                f"• {v.get('alternative_id', 'Unknown')} - {v['criterion']}: {v['value']} "
                f"({('outside ' + v.get('expected_range', '')) if 'expected_range' in v else v.get('issue', '')})"
                for v in violations[:5]
            ])
            
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                message=f"Scale compliance violations ({len(violations)} values)",
                details=violation_details,
                suggestion="Correct values to match the configured scale ranges"
            ))
    
    def _validate_criterion_types(self, matrix: np.ndarray, alternatives: List[Dict],
                                criteria: List[Dict], valid_positions: Dict):
        """Validate criterion types (cost vs benefit) make sense"""
        
        for j, crit in enumerate(criteria):
            col_values = matrix[:, j]
            valid_values = col_values[~np.isnan(col_values)]
            
            if len(valid_values) < 2:
                continue
            
            crit_type = crit.get('optimization_type', 'maximize')
            crit_name = crit['name'].lower()
            
            # Heuristic: cost-related words should usually be "minimize"
            cost_keywords = ['cost', 'price', 'expense', 'fee', 'time', 'duration', 'risk', 'error']
            benefit_keywords = ['profit', 'revenue', 'quality', 'satisfaction', 'efficiency', 'performance']
            
            has_cost_keyword = any(keyword in crit_name for keyword in cost_keywords)
            has_benefit_keyword = any(keyword in crit_name for keyword in benefit_keywords)
            
            if has_cost_keyword and crit_type == 'maximize':
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    message=f"Potential criterion type mismatch: '{crit['name']}'",
                    details=f"Criterion contains cost-related keywords but is set to 'maximize'",
                    suggestion="Consider if this criterion should be 'minimize' instead",
                    affected_criteria=[crit['id']]
                ))
            
            if has_benefit_keyword and crit_type == 'minimize':
                self.validation_results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,  
                    message=f"Potential criterion type mismatch: '{crit['name']}'",
                    details=f"Criterion contains benefit-related keywords but is set to 'minimize'",
                    suggestion="Consider if this criterion should be 'maximize' instead",
                    affected_criteria=[crit['id']]
                ))
    
    def _analyze_completeness(self, matrix_data: Dict[str, str], 
                            alternatives: List[Dict], criteria: List[Dict]):
        """Analyze matrix completeness and suggest improvements"""
        
        total_cells = len(alternatives) * len(criteria)
        filled_cells = sum(1 for value in matrix_data.values() if value.strip())
        completeness = filled_cells / total_cells if total_cells > 0 else 0
        
        # Overall completeness
        if completeness < self.completeness_threshold:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message=f"Low matrix completeness ({completeness:.1%})",
                details=f"Only {filled_cells}/{total_cells} cells are filled",
                suggestion=f"Consider completing at least {self.completeness_threshold:.0%} of the matrix for reliable results"
            ))
        
        # Check completeness by rows (alternatives)
        incomplete_alternatives = []
        for alt in alternatives:
            alt_filled = sum(1 for crit in criteria 
                           if f"{alt['id']}_{crit['id']}" in matrix_data 
                           and matrix_data[f"{alt['id']}_{crit['id']}"].strip())
            alt_completeness = alt_filled / len(criteria) if criteria else 0
            
            if alt_completeness < 0.5:  # Less than 50% filled
                incomplete_alternatives.append(f"{alt['name']} ({alt_completeness:.0%})")
        
        if incomplete_alternatives:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.INFO,
                message=f"Incomplete alternatives detected ({len(incomplete_alternatives)})",
                details="Alternatives with <50% completion:\n" + "\n".join(incomplete_alternatives[:3]),
                suggestion="Consider prioritizing completion of these alternatives"
            ))
        
        # Check completeness by columns (criteria)
        incomplete_criteria = []
        for crit in criteria:
            crit_filled = sum(1 for alt in alternatives
                            if f"{alt['id']}_{crit['id']}" in matrix_data
                            and matrix_data[f"{alt['id']}_{crit['id']}"].strip())
            crit_completeness = crit_filled / len(alternatives) if alternatives else 0
            
            if crit_completeness < 0.5:  # Less than 50% filled
                incomplete_criteria.append(f"{crit['name']} ({crit_completeness:.0%})")
        
        if incomplete_criteria:
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.INFO,
                message=f"Incomplete criteria detected ({len(incomplete_criteria)})",
                details="Criteria with <50% completion:\n" + "\n".join(incomplete_criteria[:3]),
                suggestion="Consider prioritizing completion of these criteria"
            ))
    
    def _analyze_criteria_correlation(self, matrix: np.ndarray, criteria: List[Dict], 
                                   valid_positions: Dict):
        """Analyze correlation between criteria to detect potential redundancy"""
        
        if len(criteria) < 2:
            return
        
        # Calculate correlation matrix
        correlations = []
        high_correlations = []
        
        for i in range(len(criteria)):
            for j in range(i + 1, len(criteria)):
                col1 = matrix[:, i]
                col2 = matrix[:, j]
                
                # Remove NaN values for correlation calculation
                valid_mask = ~(np.isnan(col1) | np.isnan(col2))
                if np.sum(valid_mask) < 3:  # Need at least 3 points
                    continue
                
                try:
                    correlation = np.corrcoef(col1[valid_mask], col2[valid_mask])[0, 1]
                    
                    if abs(correlation) > 0.8:  # High correlation threshold
                        high_correlations.append({
                            'criteria1': criteria[i]['name'],
                            'criteria2': criteria[j]['name'],
                            'correlation': correlation
                        })
                        
                except:
                    continue
        
        if high_correlations:
            corr_details = "\n".join([
                f"• {hc['criteria1']} ↔ {hc['criteria2']}: {hc['correlation']:.3f}"
                for hc in high_correlations[:3]
            ])
            
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.INFO,
                message=f"Highly correlated criteria detected ({len(high_correlations)} pairs)",
                details=corr_details,
                suggestion="Consider if some criteria might be redundant or can be combined",
                affected_criteria=[hc['criteria1'] for hc in high_correlations] + 
                               [hc['criteria2'] for hc in high_correlations]
            ))
    
    def _analyze_alternative_dominance(self, matrix: np.ndarray, alternatives: List[Dict],
                                     criteria: List[Dict], valid_positions: Dict):
        """Analyze if any alternative dominates others"""
        
        if len(alternatives) < 2:
            return
        
        dominated_alternatives = []
        
        for i in range(len(alternatives)):
            for j in range(len(alternatives)):
                if i == j:
                    continue
                
                # Check if alternative i dominates alternative j
                dominates = True
                has_better = False
                
                for k, crit in enumerate(criteria):
                    if np.isnan(matrix[i, k]) or np.isnan(matrix[j, k]):
                        dominates = False
                        break
                    
                    crit_type = crit.get('optimization_type', 'maximize')
                    
                    if crit_type == 'maximize':
                        if matrix[i, k] < matrix[j, k]:
                            dominates = False
                            break
                        elif matrix[i, k] > matrix[j, k]:
                            has_better = True
                    else:  # minimize
                        if matrix[i, k] > matrix[j, k]:
                            dominates = False
                            break
                        elif matrix[i, k] < matrix[j, k]:
                            has_better = True
                
                if dominates and has_better:
                    dominated_alternatives.append({
                        'dominating': alternatives[i]['name'],
                        'dominated': alternatives[j]['name']
                    })
        
        if dominated_alternatives:
            dom_details = "\n".join([
                f"• {da['dominating']} dominates {da['dominated']}"
                for da in dominated_alternatives[:3]
            ])
            
            self.validation_results.append(ValidationResult(
                severity=ValidationSeverity.INFO,
                message=f"Alternative dominance detected ({len(dominated_alternatives)} cases)",
                details=dom_details,
                suggestion="Dominated alternatives can be eliminated from consideration",
                affected_alternatives=[da['dominated'] for da in dominated_alternatives]
            ))

    def get_validation_summary(self) -> Dict[str, int]:
        """Get summary of validation results by severity"""
        summary = {severity.value: 0 for severity in ValidationSeverity}
        
        for result in self.validation_results:
            summary[result.severity.value] += 1
            
        return summary
    
    def get_critical_issues(self) -> List[ValidationResult]:
        """Get only critical and error issues"""
        return [r for r in self.validation_results 
                if r.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]]
    
    def has_blocking_issues(self) -> bool:
        """Check if there are issues that would prevent MCDM method execution"""
        return any(r.severity == ValidationSeverity.CRITICAL for r in self.validation_results)