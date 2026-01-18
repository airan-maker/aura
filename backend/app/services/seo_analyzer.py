"""SEO analysis engine for evaluating website SEO quality."""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SEOAnalyzer:
    """
    SEO Analysis Engine.

    Analyzes crawled website data and generates:
    - SEO score (0-100)
    - Category-specific scores
    - Issues list
    - Actionable recommendations

    Scoring weights:
    - Meta tags: 25%
    - Headings: 15%
    - Performance: 20%
    - Mobile: 15%
    - Security (HTTPS): 10%
    - Structured Data: 15%
    """

    WEIGHTS = {
        'meta_tags': 0.25,
        'headings': 0.15,
        'performance': 0.20,
        'mobile': 0.15,
        'security': 0.10,
        'structured_data': 0.15
    }

    # Optimal meta tag lengths
    TITLE_MIN_LENGTH = 30
    TITLE_MAX_LENGTH = 60
    DESCRIPTION_MIN_LENGTH = 120
    DESCRIPTION_MAX_LENGTH = 160

    # Performance thresholds (seconds)
    PERF_EXCELLENT = 2.0
    PERF_GOOD = 3.0
    PERF_ACCEPTABLE = 5.0

    def analyze(self, crawl_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive SEO analysis on crawled data.

        Args:
            crawl_data: Dictionary containing crawled website data

        Returns:
            Dictionary containing:
            - score: Overall SEO score (0-100)
            - category_scores: Scores for each category
            - issues: List of identified issues
            - recommendations: List of actionable recommendations
            - metrics: Detailed SEO metrics
        """
        logger.info(f"Starting SEO analysis for {crawl_data.get('url', 'unknown')}")

        scores = {}
        issues = []
        recommendations = []

        # 1. Meta tags analysis
        meta_analysis = self._analyze_meta_tags(crawl_data.get('meta_tags', {}))
        scores['meta_tags'] = meta_analysis['score']
        issues.extend(meta_analysis['issues'])
        recommendations.extend(meta_analysis['recommendations'])

        # 2. Headings analysis
        heading_analysis = self._analyze_headings(crawl_data.get('headings', {}))
        scores['headings'] = heading_analysis['score']
        issues.extend(heading_analysis['issues'])
        recommendations.extend(heading_analysis.get('recommendations', []))

        # 3. Performance analysis
        perf_analysis = self._analyze_performance(crawl_data.get('load_time', 0))
        scores['performance'] = perf_analysis['score']
        if perf_analysis.get('issue'):
            issues.append(perf_analysis['issue'])
        recommendations.extend(perf_analysis.get('recommendations', []))

        # 4. Mobile friendliness
        mobile_score, mobile_recs = self._analyze_mobile(crawl_data.get('mobile_friendly', False))
        scores['mobile'] = mobile_score
        recommendations.extend(mobile_recs)

        # 5. Security (HTTPS)
        security_score, security_recs = self._analyze_security(crawl_data.get('ssl_enabled', False))
        scores['security'] = security_score
        recommendations.extend(security_recs)

        # 6. Structured Data
        sd_analysis = self._analyze_structured_data(crawl_data.get('structured_data', []))
        scores['structured_data'] = sd_analysis['score']
        recommendations.extend(sd_analysis.get('recommendations', []))

        # Calculate overall score (weighted average)
        total_score = sum(scores[key] * self.WEIGHTS[key] for key in scores)

        logger.info(f"SEO analysis complete. Overall score: {total_score:.2f}")

        return {
            'score': round(total_score, 2),
            'category_scores': scores,
            'issues': issues,
            'recommendations': recommendations,
            'metrics': {
                'meta_tags': crawl_data.get('meta_tags', {}),
                'headings': crawl_data.get('headings', {}),
                'load_time': crawl_data.get('load_time', 0),
                'mobile_friendly': crawl_data.get('mobile_friendly', False),
                'ssl_enabled': crawl_data.get('ssl_enabled', False),
                'structured_data': crawl_data.get('structured_data', [])
            }
        }

    def _analyze_meta_tags(self, meta_tags: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze meta tags quality.

        Checks:
        - Title tag presence and length
        - Meta description presence and length
        - Open Graph tags
        - Canonical URL

        Args:
            meta_tags: Dictionary of meta tags

        Returns:
            Dictionary with score, issues, and recommendations
        """
        score = 0
        issues = []
        recommendations = []

        # Title tag analysis (40 points)
        title = meta_tags.get('title', '')
        if not title:
            issues.append("Missing title tag")
            recommendations.append({
                'category': 'seo',
                'priority': 'critical',
                'title': 'Add Title Tag',
                'description': 'Every page must have a unique, descriptive title tag (30-60 characters)',
                'impact': 'high'
            })
        elif len(title) < self.TITLE_MIN_LENGTH:
            issues.append(f"Title too short ({len(title)} chars, recommended: {self.TITLE_MIN_LENGTH}-{self.TITLE_MAX_LENGTH})")
            score += 20
            recommendations.append({
                'category': 'seo',
                'priority': 'high',
                'title': 'Expand Title Tag',
                'description': f'Your title is only {len(title)} characters. Expand it to 30-60 characters for better SEO.',
                'impact': 'medium'
            })
        elif len(title) > self.TITLE_MAX_LENGTH:
            issues.append(f"Title too long ({len(title)} chars, recommended: {self.TITLE_MIN_LENGTH}-{self.TITLE_MAX_LENGTH})")
            score += 30
            recommendations.append({
                'category': 'seo',
                'priority': 'medium',
                'title': 'Shorten Title Tag',
                'description': f'Your title is {len(title)} characters. Shorten it to 60 characters or less to avoid truncation in search results.',
                'impact': 'medium'
            })
        else:
            score += 40

        # Meta description analysis (40 points)
        description = meta_tags.get('description', '')
        if not description:
            issues.append("Missing meta description")
            recommendations.append({
                'category': 'seo',
                'priority': 'high',
                'title': 'Add Meta Description',
                'description': 'Add a compelling meta description (120-160 characters) to improve click-through rates from search results.',
                'impact': 'high'
            })
        elif len(description) < self.DESCRIPTION_MIN_LENGTH:
            issues.append(f"Description too short ({len(description)} chars)")
            score += 20
            recommendations.append({
                'category': 'seo',
                'priority': 'medium',
                'title': 'Expand Meta Description',
                'description': f'Your meta description is only {len(description)} characters. Expand it to 120-160 characters for better engagement.',
                'impact': 'medium'
            })
        elif len(description) > self.DESCRIPTION_MAX_LENGTH:
            issues.append(f"Description too long ({len(description)} chars)")
            score += 30
        else:
            score += 40

        # Open Graph tags (10 points)
        og_tags = [k for k in meta_tags.keys() if k.startswith('og:')]
        if len(og_tags) >= 4:  # og:title, og:description, og:image, og:url
            score += 10
        elif len(og_tags) > 0:
            score += 5
            recommendations.append({
                'category': 'seo',
                'priority': 'low',
                'title': 'Complete Open Graph Tags',
                'description': 'Add complete Open Graph tags (og:title, og:description, og:image, og:url) to improve social media sharing.',
                'impact': 'low'
            })
        else:
            recommendations.append({
                'category': 'seo',
                'priority': 'medium',
                'title': 'Add Open Graph Tags',
                'description': 'Add Open Graph meta tags to control how your content appears when shared on social media platforms.',
                'impact': 'medium'
            })

        # Canonical URL (10 points)
        if 'canonical' in meta_tags:
            score += 10
        else:
            recommendations.append({
                'category': 'seo',
                'priority': 'low',
                'title': 'Add Canonical URL',
                'description': 'Add a canonical link tag to prevent duplicate content issues.',
                'impact': 'low'
            })

        return {
            'score': min(score, 100),
            'issues': issues,
            'recommendations': recommendations
        }

    def _analyze_headings(self, headings: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Analyze heading structure quality.

        Checks:
        - H1 tag presence and uniqueness
        - Heading hierarchy
        - H2 presence

        Args:
            headings: Dictionary of heading levels (h1-h6)

        Returns:
            Dictionary with score and issues
        """
        score = 100
        issues = []
        recommendations = []

        # H1 analysis (50 points)
        h1_count = len(headings.get('h1', []))
        if h1_count == 0:
            score -= 50
            issues.append("Missing H1 tag")
            recommendations.append({
                'category': 'seo',
                'priority': 'critical',
                'title': 'Add H1 Heading',
                'description': 'Every page must have exactly one H1 tag that describes the main topic.',
                'impact': 'high'
            })
        elif h1_count > 1:
            score -= 20
            issues.append(f"Multiple H1 tags found ({h1_count}), should have only one")
            recommendations.append({
                'category': 'seo',
                'priority': 'high',
                'title': 'Use Single H1 Tag',
                'description': f'You have {h1_count} H1 tags. Use only one H1 per page for better SEO.',
                'impact': 'medium'
            })

        # H2 presence (30 points)
        h2_count = len(headings.get('h2', []))
        if h2_count == 0 and h1_count > 0:
            score -= 30
            issues.append("No H2 tags found - consider adding subheadings")
            recommendations.append({
                'category': 'seo',
                'priority': 'medium',
                'title': 'Add H2 Subheadings',
                'description': 'Add H2 tags to structure your content with clear subheadings.',
                'impact': 'medium'
            })

        # Heading hierarchy check (20 points)
        has_proper_hierarchy = True
        for i in range(1, 6):
            current_level = f'h{i}'
            next_level = f'h{i+1}'
            if len(headings.get(next_level, [])) > 0 and len(headings.get(current_level, [])) == 0:
                has_proper_hierarchy = False
                issues.append(f"Heading hierarchy issue: {next_level.upper()} found without {current_level.upper()}")
                break

        if not has_proper_hierarchy:
            score -= 20
            recommendations.append({
                'category': 'seo',
                'priority': 'low',
                'title': 'Fix Heading Hierarchy',
                'description': 'Maintain proper heading hierarchy (H1 → H2 → H3) without skipping levels.',
                'impact': 'low'
            })

        return {
            'score': max(score, 0),
            'issues': issues,
            'recommendations': recommendations
        }

    def _analyze_performance(self, load_time: float) -> Dict[str, Any]:
        """
        Analyze page load performance.

        Args:
            load_time: Page load time in seconds

        Returns:
            Dictionary with score, issue, and recommendations
        """
        recommendations = []

        if load_time < self.PERF_EXCELLENT:
            score = 100
            issue = None
        elif load_time < self.PERF_GOOD:
            score = 80
            issue = f"Page load time ({load_time:.2f}s) is acceptable but could be improved"
            recommendations.append({
                'category': 'seo',
                'priority': 'low',
                'title': 'Optimize Page Speed',
                'description': f'Your page loads in {load_time:.2f} seconds. Consider optimizing images and minifying resources to reach under 2 seconds.',
                'impact': 'low'
            })
        elif load_time < self.PERF_ACCEPTABLE:
            score = 50
            issue = f"Page load time ({load_time:.2f}s) is slow"
            recommendations.append({
                'category': 'seo',
                'priority': 'high',
                'title': 'Improve Page Speed',
                'description': f'Your page takes {load_time:.2f} seconds to load. Optimize images, enable caching, and minify CSS/JS to improve speed.',
                'impact': 'high'
            })
        else:
            score = 20
            issue = f"Page load time ({load_time:.2f}s) is very slow"
            recommendations.append({
                'category': 'seo',
                'priority': 'critical',
                'title': 'Critical: Fix Page Speed',
                'description': f'Your page takes {load_time:.2f} seconds to load, which severely impacts SEO and user experience. Prioritize speed optimization.',
                'impact': 'critical'
            })

        return {
            'score': score,
            'issue': issue,
            'recommendations': recommendations
        }

    def _analyze_mobile(self, mobile_friendly: bool) -> tuple[int, List[Dict[str, Any]]]:
        """
        Analyze mobile friendliness.

        Args:
            mobile_friendly: Whether viewport meta tag is present

        Returns:
            Tuple of (score, recommendations)
        """
        recommendations = []

        if mobile_friendly:
            return 100, recommendations
        else:
            recommendations.append({
                'category': 'seo',
                'priority': 'critical',
                'title': 'Add Viewport Meta Tag',
                'description': 'Add <meta name="viewport" content="width=device-width, initial-scale=1"> to make your site mobile-friendly. Mobile-first indexing requires this.',
                'impact': 'critical'
            })
            return 0, recommendations

    def _analyze_security(self, ssl_enabled: bool) -> tuple[int, List[Dict[str, Any]]]:
        """
        Analyze security (HTTPS).

        Args:
            ssl_enabled: Whether site uses HTTPS

        Returns:
            Tuple of (score, recommendations)
        """
        recommendations = []

        if ssl_enabled:
            return 100, recommendations
        else:
            recommendations.append({
                'category': 'seo',
                'priority': 'critical',
                'title': 'Enable HTTPS',
                'description': 'Switch to HTTPS to secure your site. Google prioritizes HTTPS sites in search rankings and browsers mark HTTP sites as "Not Secure".',
                'impact': 'critical'
            })
            return 0, recommendations

    def _analyze_structured_data(self, structured_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze structured data (Schema.org).

        Args:
            structured_data: List of JSON-LD structured data objects

        Returns:
            Dictionary with score and recommendations
        """
        recommendations = []

        if not structured_data:
            recommendations.append({
                'category': 'seo',
                'priority': 'medium',
                'title': 'Add Structured Data',
                'description': 'Add Schema.org structured data (JSON-LD) to help search engines understand your content better and enable rich snippets.',
                'impact': 'medium'
            })
            return {'score': 0, 'recommendations': recommendations}

        # Check for valid schema types
        valid_types = ['Organization', 'WebSite', 'Article', 'Product', 'LocalBusiness', 'FAQPage', 'BreadcrumbList']
        has_valid_schema = False

        for item in structured_data:
            item_type = item.get('@type', '')
            if isinstance(item_type, list):
                item_type = item_type[0] if item_type else ''

            if item_type in valid_types:
                has_valid_schema = True
                break

        if has_valid_schema:
            score = 100
        else:
            score = 50
            recommendations.append({
                'category': 'seo',
                'priority': 'low',
                'title': 'Improve Structured Data',
                'description': f'Consider adding more specific schema types like Organization, Product, or Article for better search engine understanding.',
                'impact': 'low'
            })

        return {'score': score, 'recommendations': recommendations}


def analyze_seo(crawl_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze SEO.

    Args:
        crawl_data: Crawled website data

    Returns:
        SEO analysis results

    Example:
        >>> from app.services.crawler import crawl_url
        >>> from app.services.seo_analyzer import analyze_seo
        >>>
        >>> crawl_data = await crawl_url("https://example.com")
        >>> seo_results = analyze_seo(crawl_data)
        >>> print(f"SEO Score: {seo_results['score']}")
    """
    analyzer = SEOAnalyzer()
    return analyzer.analyze(crawl_data)
