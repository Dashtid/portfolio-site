"""
Content Verification Script for Phase 7
Compares API data from migration against expected content
"""
import json
import requests
from typing import Dict, List

API_BASE = "http://localhost:8001/api/v1"

def verify_companies() -> Dict:
    """Verify all companies data"""
    print("[*] Verifying Companies API...")

    try:
        response = requests.get(f"{API_BASE}/companies/")
        response.raise_for_status()
        companies = response.json()

        print(f"[OK] Companies API returned HTTP 200")
        print(f"[OK] Total companies: {len(companies)}")

        # Expected companies from original portfolio
        expected = [
            "Hermes Medical Solutions",
            "Scania Engines",
            "Finnish Defence Forces",
            "Södersjukhuset - SÖS",
            "SoftPro Medical Solutions",
            "Karolinska University Hospital",
            "Philips Healthcare"
        ]

        found_names = [c['name'] for c in companies]

        # Check all expected companies present
        missing = []
        for exp in expected:
            if exp not in found_names:
                missing.append(exp)

        if missing:
            print(f"[FAIL] Missing companies: {missing}")
            return {"status": "FAIL", "missing": missing, "total": len(companies)}
        else:
            print(f"[OK] All 7 expected companies found")

        # Verify each company has required fields
        issues = []
        for i, company in enumerate(companies, 1):
            print(f"\n--- Company {i}: {company['name']} ---")
            print(f"  Title: {company.get('title', 'MISSING')}")
            print(f"  Location: {company.get('location', 'MISSING')}")
            print(f"  Dates: {company.get('start_date')} to {company.get('end_date') or 'Present'}")
            print(f"  Logo: {company.get('logo_url', 'MISSING')}")

            # Check required fields
            if not company.get('name'):
                issues.append(f"{company['id']}: missing name")
            if not company.get('description'):
                issues.append(f"{company['name']}: missing description")
            if not company.get('logo_url'):
                issues.append(f"{company['name']}: missing logo_url")

        if issues:
            print(f"\n[WARN] Field issues found: {len(issues)}")
            for issue in issues:
                print(f"  - {issue}")

        return {
            "status": "PASS" if not missing and not issues else "WARN",
            "total": len(companies),
            "expected": len(expected),
            "missing": missing,
            "issues": issues
        }

    except Exception as e:
        print(f"[FAIL] Companies API error: {type(e).__name__}: {e}")
        return {"status": "FAIL", "error": str(e)}

def verify_projects() -> Dict:
    """Verify all projects data"""
    print("\n[*] Verifying Projects API...")

    try:
        response = requests.get(f"{API_BASE}/projects/")
        response.raise_for_status()
        projects = response.json()

        print(f"[OK] Projects API returned HTTP 200")
        print(f"[OK] Total projects: {len(projects)}")

        # Verify each project has required fields
        issues = []
        for i, project in enumerate(projects, 1):
            print(f"\n--- Project {i}: {project['name']} ---")
            print(f"  Description: {project.get('description', 'MISSING')[:50]}...")
            print(f"  Technologies: {len(project.get('technologies', []))} items")
            print(f"  Featured: {project.get('featured', False)}")

            # Check required fields
            if not project.get('name'):
                issues.append(f"Project {project.get('id')}: missing name")
            if not project.get('description'):
                issues.append(f"{project['name']}: missing description")
            if not project.get('technologies'):
                issues.append(f"{project['name']}: missing technologies")

        if issues:
            print(f"\n[WARN] Field issues found: {len(issues)}")
            for issue in issues:
                print(f"  - {issue}")

        return {
            "status": "PASS" if not issues else "WARN",
            "total": len(projects),
            "issues": issues
        }

    except Exception as e:
        print(f"[FAIL] Projects API error: {type(e).__name__}: {e}")
        return {"status": "FAIL", "error": str(e)}

def verify_education() -> Dict:
    """Verify all education data"""
    print("\n[*] Verifying Education API...")

    try:
        response = requests.get(f"{API_BASE}/education/")
        response.raise_for_status()
        education = response.json()

        print(f"[OK] Education API returned HTTP 200")
        print(f"[OK] Total education entries: {len(education)}")

        # Expected education entries
        expected_count = 4

        if len(education) != expected_count:
            print(f"[WARN] Expected {expected_count} education entries, found {len(education)}")

        # Verify each entry has required fields
        issues = []
        for i, edu in enumerate(education, 1):
            print(f"\n--- Education {i}: {edu['institution']} ---")
            print(f"  Degree: {edu.get('degree', 'MISSING')}")
            print(f"  Field: {edu.get('field_of_study', 'MISSING')}")
            print(f"  Logo: {edu.get('logo_url', 'MISSING')}")

            # Check required fields
            if not edu.get('institution'):
                issues.append(f"Entry {i}: missing institution")
            if not edu.get('degree'):
                issues.append(f"{edu.get('institution')}: missing degree")
            if not edu.get('logo_url'):
                issues.append(f"{edu.get('institution')}: missing logo_url")

        if issues:
            print(f"\n[WARN] Field issues found: {len(issues)}")
            for issue in issues:
                print(f"  - {issue}")

        return {
            "status": "PASS" if not issues else "WARN",
            "total": len(education),
            "expected": expected_count,
            "issues": issues
        }

    except Exception as e:
        print(f"[FAIL] Education API error: {type(e).__name__}: {e}")
        return {"status": "FAIL", "error": str(e)}

def main():
    """Run all verification checks"""
    print("=" * 60)
    print("PHASE 7 CONTENT VERIFICATION")
    print("=" * 60)

    results = {}

    # Verify Companies
    results['companies'] = verify_companies()

    # Verify Projects
    results['projects'] = verify_projects()

    # Verify Education
    results['education'] = verify_education()

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_pass = True
    for category, result in results.items():
        status = result.get('status', 'UNKNOWN')
        print(f"{category.upper()}: {status}")
        if status != "PASS":
            all_pass = False

    if all_pass:
        print("\n[OK] All content verification checks PASSED")
        return 0
    else:
        print("\n[WARN] Some checks have warnings or failures - review above")
        return 1

if __name__ == "__main__":
    exit(main())
