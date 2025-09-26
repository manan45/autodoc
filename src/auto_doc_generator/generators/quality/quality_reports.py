"""
Quality report generator.

This module generates comprehensive quality reports from quality analysis results,
including metrics visualizations and detailed assessments.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import json

from ..base.base_generator import BaseGenerator


class QualityReportGenerator(BaseGenerator):
    """
    Generator that creates quality reports from quality analysis data.
    """
    
    def __init__(self, config: Dict[str, Any], output_dir: str = "docs"):
        # Initialize with proper parameter order for BaseGenerator  
        super().__init__(template_dir="quality_templates", output_dir=output_dir, config=config)
        self.quality_config = config.get('quality', {})
        
    def generate(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quality reports from analysis data.
        
        Args:
            analysis_data: Combined analysis results including quality analysis
            
        Returns:
            Dictionary containing generated quality reports
        """
        self.log_generation_start("Quality Reports")
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        try:
            quality_analysis = analysis_data.get('quality_analysis', {})
            code_analysis = analysis_data.get('code_analysis', {})
            
            if not quality_analysis:
                result['errors'].append("No quality analysis data available")
                return result
            
            reports = {}
            
            # Generate main quality report
            reports['quality_overview.html'] = self.generate_quality_overview(quality_analysis)
            
            # Generate detailed module reports
            module_reports = self.generate_module_reports(quality_analysis)
            reports.update(module_reports)
            
            # Generate quality trends report
            reports['quality_trends.html'] = self.generate_quality_trends(quality_analysis)
            
            # Generate quality metrics dashboard
            reports['quality_dashboard.html'] = self.generate_quality_dashboard(quality_analysis)
            
            # Generate quality data files (JSON)
            reports['quality_data.json'] = json.dumps(quality_analysis, indent=2)
            
            result['results'] = {
                'reports': reports,
                'total_reports': len(reports),
                'output_directory': str(self.output_dir)
            }
            
            self.log_generation_complete("Quality Reports", len(reports))
            
        except Exception as e:
            result['errors'].append(f"Quality report generation failed: {str(e)}")
            self.logger.error(f"Quality report generation error: {e}")
        
        return result
    
    def generate_quality_overview(self, quality_analysis: Dict[str, Any]) -> str:
        """Generate the main quality overview report."""
        overview = quality_analysis.get('overview', {})
        distribution = quality_analysis.get('quality_distribution', {})
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Quality Overview</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 40px; 
            border-bottom: 2px solid #e0e0e0; 
            padding-bottom: 20px; 
        }}
        .metrics-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 40px; 
        }}
        .metric-card {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            text-align: center; 
            border-left: 4px solid #007bff; 
        }}
        .metric-value {{ 
            font-size: 2em; 
            font-weight: bold; 
            color: #333; 
        }}
        .metric-label {{ 
            color: #666; 
            margin-top: 5px; 
        }}
        .quality-bar {{ 
            height: 20px; 
            background: #e0e0e0; 
            border-radius: 10px; 
            overflow: hidden; 
            margin: 10px 0; 
        }}
        .quality-fill {{ 
            height: 100%; 
            background: linear-gradient(90deg, #ff4444, #ffaa00, #00aa00); 
        }}
        .distribution-table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px; 
        }}
        .distribution-table th, .distribution-table td {{ 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #ddd; 
        }}
        .distribution-table th {{ 
            background-color: #f8f9fa; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 Code Quality Overview</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{overview.get('total_modules', 0)}</div>
                <div class="metric-label">Total Modules</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{overview.get('average_quality_score', 0):.3f}</div>
                <div class="metric-label">Average Quality Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{overview.get('max_quality_score', 0):.3f}</div>
                <div class="metric-label">Highest Quality Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{overview.get('min_quality_score', 0):.3f}</div>
                <div class="metric-label">Lowest Quality Score</div>
            </div>
        </div>
        
        <div style="margin-bottom: 40px;">
            <h2>📊 Quality Distribution</h2>
"""
        
        # Add quality distribution
        ranges = distribution.get('quality_ranges', {})
        if ranges:
            html += '<table class="distribution-table">'
            html += '<tr><th>Quality Level</th><th>Module Count</th><th>Percentage</th></tr>'
            
            total_modules = sum(ranges.values())
            for level, count in ranges.items():
                percentage = (count / total_modules * 100) if total_modules > 0 else 0
                html += f'<tr><td>{level.title()}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>'
            
            html += '</table>'
        
        html += """
        </div>
        
        <div>
            <h2>📈 Overall Quality Score</h2>
            <div class="quality-bar">
                <div class="quality-fill" style="width: {:.1f}%"></div>
            </div>
            <p style="text-align: center; color: #666;">
                Quality Score: {:.3f} / 1.000
            </p>
        </div>
    </div>
</body>
</html>""".format(
            overview.get('average_quality_score', 0) * 100,
            overview.get('average_quality_score', 0)
        )
        
        return html
    
    def generate_module_reports(self, quality_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate detailed reports for individual modules."""
        reports = {}
        assessments = quality_analysis.get('module_assessments', {})
        
        # Generate reports for top modules only (to avoid too many files)
        sorted_modules = sorted(
            assessments.items(),
            key=lambda x: x[1].get('overall_score', 0),
            reverse=True
        )
        
        max_reports = self.quality_config.get('max_module_reports', 10)
        for module_path, assessment in sorted_modules[:max_reports]:
            report_filename = f"quality_module_{module_path.replace('/', '_').replace('.', '_')}.html"
            reports[report_filename] = self.generate_single_module_report(module_path, assessment)
        
        return reports
    
    def generate_single_module_report(self, module_path: str, assessment: Dict[str, Any]) -> str:
        """Generate a detailed report for a single module."""
        metrics = assessment.get('metrics', {})
        issues = assessment.get('issues', [])
        overall_score = assessment.get('overall_score', 0)
        grade = assessment.get('grade', 'F')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quality Report - {module_path}</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }}
        .header {{ 
            text-align: center; 
            margin-bottom: 30px; 
            border-bottom: 2px solid #e0e0e0; 
            padding-bottom: 20px; 
        }}
        .score-badge {{ 
            display: inline-block; 
            padding: 10px 20px; 
            border-radius: 20px; 
            font-weight: bold; 
            font-size: 1.2em; 
        }}
        .grade-A {{ background-color: #d4edda; color: #155724; }}
        .grade-B {{ background-color: #d1ecf1; color: #0c5460; }}
        .grade-C {{ background-color: #fff3cd; color: #856404; }}
        .grade-D {{ background-color: #f8d7da; color: #721c24; }}
        .grade-F {{ background-color: #f5c6cb; color: #721c24; }}
        .metrics-section {{ margin-bottom: 30px; }}
        .metric-row {{ 
            display: flex; 
            justify-content: space-between; 
            padding: 10px; 
            border-bottom: 1px solid #eee; 
        }}
        .issues-section {{ margin-bottom: 30px; }}
        .issue-item {{ 
            padding: 10px; 
            margin: 10px 0; 
            border-left: 4px solid #ffc107; 
            background-color: #fff3cd; 
        }}
        .issue-major {{ border-left-color: #dc3545; background-color: #f8d7da; }}
        .issue-minor {{ border-left-color: #28a745; background-color: #d4edda; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Quality Report</h1>
            <h2>{module_path}</h2>
            <div class="score-badge grade-{grade}">
                Grade: {grade} | Score: {overall_score:.3f}
            </div>
        </div>
        
        <div class="metrics-section">
            <h3>📈 Metrics</h3>
"""
        
        # Add metrics
        metric_labels = {
            'lines_of_code': 'Lines of Code',
            'function_count': 'Functions',
            'class_count': 'Classes',
            'avg_complexity': 'Average Complexity',
            'max_complexity': 'Max Complexity',
            'documentation_coverage': 'Documentation Coverage',
            'comment_ratio': 'Comment Ratio'
        }
        
        for metric_key, metric_label in metric_labels.items():
            value = metrics.get(metric_key, 0)
            if metric_key in ['documentation_coverage', 'comment_ratio']:
                display_value = f"{value:.1%}"
            elif metric_key in ['avg_complexity']:
                display_value = f"{value:.2f}"
            else:
                display_value = str(int(value)) if isinstance(value, (int, float)) else str(value)
            
            html += f"""
            <div class="metric-row">
                <span>{metric_label}</span>
                <span><strong>{display_value}</strong></span>
            </div>"""
        
        html += """
        </div>
        
        <div class="issues-section">
            <h3>⚠️ Issues Found</h3>
"""
        
        if issues:
            for issue in issues:
                severity_class = f"issue-{issue.get('severity', 'minor')}"
                html += f"""
            <div class="issue-item {severity_class}">
                <strong>Line {issue.get('line', '?')}</strong>: {issue.get('message', 'Unknown issue')}
                <br><small>Type: {issue.get('type', 'unknown')} | Severity: {issue.get('severity', 'minor')}</small>
            </div>"""
        else:
            html += '<p>✅ No issues found!</p>'
        
        html += """
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def generate_quality_trends(self, quality_analysis: Dict[str, Any]) -> str:
        """Generate quality trends report (placeholder for now)."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quality Trends</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Quality Trends</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div style="text-align: center; padding: 50px;">
            <h2>🚧 Coming Soon</h2>
            <p>Quality trends tracking will be available in future versions.</p>
            <p>This will show quality improvements over time, regression detection, and historical comparisons.</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def generate_quality_dashboard(self, quality_analysis: Dict[str, Any]) -> str:
        """Generate interactive quality dashboard."""
        overview = quality_analysis.get('overview', {})
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quality Dashboard</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5; 
        }}
        .container {{ 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }}
        .dashboard-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }}
        .dashboard-card {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            border-left: 4px solid #007bff; 
        }}
        .chart-placeholder {{ 
            height: 200px; 
            background: #e9ecef; 
            border-radius: 4px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            color: #6c757d; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Quality Dashboard</h1>
        <p>Interactive quality metrics and visualizations</p>
        
        <div class="dashboard-grid">
            <div class="dashboard-card">
                <h3>📈 Quality Score Trend</h3>
                <div class="chart-placeholder">
                    Quality Score: {overview.get('average_quality_score', 0):.3f}
                    <br>Chart visualization coming soon
                </div>
            </div>
            
            <div class="dashboard-card">
                <h3>🎯 Module Distribution</h3>
                <div class="chart-placeholder">
                    Total Modules: {overview.get('total_modules', 0)}
                    <br>Distribution chart coming soon
                </div>
            </div>
            
            <div class="dashboard-card">
                <h3>⚠️ Issues Overview</h3>
                <div class="chart-placeholder">
                    Issues tracking
                    <br>Coming soon
                </div>
            </div>
            
            <div class="dashboard-card">
                <h3>📊 Complexity Metrics</h3>
                <div class="chart-placeholder">
                    Complexity analysis
                    <br>Coming soon
                </div>
            </div>
        </div>
        
        <div style="text-align: center; padding: 30px; background: #e9ecef; border-radius: 8px;">
            <h3>🚀 Enhanced Dashboard Features</h3>
            <p>Future versions will include:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>Interactive charts and graphs</li>
                <li>Real-time quality monitoring</li>
                <li>Customizable quality thresholds</li>
                <li>Quality improvement recommendations</li>
                <li>Historical trend analysis</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def save_reports(self, reports: Dict[str, str]):
        """
        Save generated reports to files.
        
        Args:
            reports: Dictionary mapping filenames to content
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, content in reports.items():
            output_path = self.output_dir / filename
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.logger.info(f"Saved quality report: {filename}")
            except Exception as e:
                self.logger.error(f"Failed to save report {filename}: {e}")
