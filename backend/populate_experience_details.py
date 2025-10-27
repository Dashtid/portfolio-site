"""
Populate database with detailed experience page content.

This script adds video URLs, map URLs, and detailed descriptions
for the 6 major companies that have detailed experience pages in
the original portfolio-site.

Run from backend directory:
    python populate_experience_details.py
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "portfolio.db"

# Detailed experience data extracted from portfolio-site/experience/ HTML files
EXPERIENCE_DETAILS = {
    "Hermes Medical Solutions": {
        "video_url": "https://www.youtube.com/embed/bdbevZrjdtU",
        "video_title": "HERMIA – ALL-IN-ONE Molecular Imaging Software",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d23019.922985510006!2d17.999845284557612!3d59.338079926240894!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f77fcd4b7b5e1%3A0xf7dcf06b9ce62c50!2sHermes%20Medical%20Solutions%20AB!5e0!3m2!1ssv!2sse!4v1749928857261!5m2!1ssv!2sse",
        "map_title": "Hermes Medical Solutions AB Location",
        "detailed_description": """Hermes Medical Solutions is a healthcare technology company that develops software solutions for nuclear medicine, supporting medical professionals with diagnostic imaging and treatment planning tools.

In my role at Hermes Medical Solutions, I work as a multidisciplinary specialist focused on quality assurance, regulatory compliance, and cybersecurity for nuclear medicine software.

**Regulatory Compliance and Market Access:** I ensure our software meets regulatory requirements including NIS2 and ISO 27001 standards for the European healthcare market. I support market clearance processes and help navigate regulatory requirements across different jurisdictions while maintaining our competitive edge.

**Quality Assurance and Validation:** I lead Verification & Validation (V&V) activities that ensure our software meets quality standards. Given that nuclear medicine software impacts patient diagnosis and treatment, I maintain rigorous testing protocols and documentation to meet both internal and external requirements.

**Technical Development and Integration:** I work with complex software systems, particularly those involving DICOM protocols and enterprise architectures. My technical experience includes Windows Server, Docker, PowerShell, Git, and Python for developing testing tools and automation solutions.

**Data Security:** I work with data security, ensuring company and customer data is protected through appropriate controls and policies. This includes assessing security practices, implementing internal best practices, and maintaining data protection standards for our development and testing environments.

**Cross-Functional Collaboration:** Working in a hybrid environment, I collaborate with development teams, clinical specialists, and regulatory experts to align technical excellence with clinical needs and regulatory requirements.""",
    },
    "Karolinska University Hospital": {
        "video_url": "https://www.youtube.com/embed/05k9c4zPBWo",
        "video_title": "Karolinska Universitetssjukhuset",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d27373.793052339282!2d18.003493380951838!3d59.34014358751482!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f9d5fc509b8cd%3A0x6f2520b3e07808ba!2sKarolinska%20Universitetssjukhuset%20Solna!5e0!3m2!1ssv!2sse!4v1749832921700!5m2!1ssv!2sse",
        "map_title": "Karolinska Universitetssjukhuset Solna Location",
        "detailed_description": """Karolinska University Hospital is one of Europe's largest and most prestigious university hospitals, serving as both a leading healthcare provider and a major research institution affiliated with the Karolinska Institute, home to the Nobel Prize in Physiology or Medicine. The hospital is renowned for its cutting-edge medical technology and innovative patient care approaches.

During my time at Karolinska University Hospital, I operated at the intersection of advanced medical technology and patient care, ensuring seamless operation of sophisticated imaging systems that directly impact diagnostic accuracy and treatment outcomes.

**Comprehensive Equipment Support:** Served as the primary technical resource for the hospital's entire fleet of medical imaging equipment, providing first-line support across multiple modalities and vendor platforms. This responsibility required maintaining operational readiness of diagnostic tools that healthcare professionals depend on for patient care, demanding both rapid response capabilities and deep technical expertise across diverse imaging technologies.

**Multi-Vendor Technology Integration:** Worked extensively with advanced visualization solutions from major medical technology vendors including GE, Philips, and Siemens, developing comprehensive understanding of how different systems integrate within the hospital's complex technical ecosystem. This experience provided valuable insight into vendor-specific architectures while maintaining system interoperability across the entire imaging infrastructure.

**Systems Architecture and Integration:** Developed understanding of clinical and technical workflows for RIS/PACS integrations with the regional Hospital Information System (HIS). This work involved learning system architectures that support imaging solutions in clinical environments. Gained experience with healthcare communication protocols including DICOM and HL7, which are essential for medical imaging workflows.

**Infrastructure and Process Management:** Enhanced technical capabilities through hands-on experience with Active Directory management and ITIL framework implementation for technical support processes.""",
    },
    "Philips Healthcare": {
        "video_url": "https://www.youtube.com/embed/i2wsMvBen1c",
        "video_title": "Enterprise Informatics ESC 2023",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d32535.951427291504!2d17.999412838149354!3d59.35804439018847!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f9e93436d98c5%3A0x16230b74d42df0ca!2sPhilips%20AB!5e0!3m2!1ssv!2sse!4v1749928636549!5m2!1ssv!2sse",
        "map_title": "Philips AB Location",
        "detailed_description": """Philips is a global leader in health technology, developing innovative solutions that improve patient outcomes and healthcare delivery worldwide. Within their Enterprise Informatics division, Philips creates sophisticated software platforms that enable healthcare professionals to visualize, analyze, and manage medical imaging data across entire hospital networks.

During my tenure at Philips, I served as a critical link between cutting-edge medical imaging technology and healthcare providers across Northern Europe, ensuring that advanced diagnostic tools remained operational and effective in clinical environments where patient care depends on reliable system performance.

**Specialized System Support:** Provided comprehensive Level 1 support for two flagship Enterprise Informatics platforms: Intellispace Portal (ISP), a sophisticated application suite enabling advanced visualization and image processing of clinical images, and Intellispace Cardiovascular (ISCV), a specialized PACS solution designed specifically for cardiology informatics. This dual-system expertise required deep understanding of both general medical imaging workflows and the specialized requirements of cardiovascular diagnostics.

**Independent Problem Resolution:** Operating in a stand-alone capacity within my team, I managed the complete incident lifecycle from initial customer contact through resolution or appropriate escalation. This autonomous role demanded strong decision-making skills and technical judgment to determine when issues could be resolved at Level 1 versus when they required escalation to Level 2 or Level 3 specialist teams. The position required balancing rapid response times with thorough problem analysis to ensure customer satisfaction.

**Deployment Quality Assurance:** Collaborated closely with upgrade and installation teams to evaluate system deployment success and identify improvement opportunities. This cross-functional work involved analyzing deployment outcomes, gathering customer feedback, and contributing to process refinements that enhanced overall customer satisfaction with Philips products. The role required understanding both technical implementation challenges and customer experience factors.

**Regional Leadership and Mentorship:** Managed primary responsibility for the Nordic region while maintaining a dotted-line relationship to UK & Ireland operations, providing support to remote service teams as needed. Additionally, served as an integral member of a Level 1 team that bridged UK & Ireland and Nordic operations, focusing on team development and knowledge sharing. This leadership component involved mentoring fellow Level 1 engineers, driving team performance improvements, and fostering professional growth across the international team.

**International Operations and Technical Development:** Gained valuable international experience managing service delivery across diverse healthcare systems and regulatory environments in both Nordic and UK & Ireland regions. Enhanced technical expertise in critical healthcare IT protocols including HL7, broker engines, and enterprise architecture solutions, while developing advanced troubleshooting capabilities and stakeholder management skills essential for supporting complex medical imaging infrastructures.

**Customer-Centric Process Improvement:** Maintained unwavering focus on customer satisfaction throughout all activities, working systematically to improve system deployment processes and service delivery quality, ensuring that Philips' advanced medical imaging solutions consistently met the demanding requirements of modern healthcare environments.""",
    },
    "Scania Engines": {
        "video_url": "https://www.youtube.com/embed/Rm6grXvyX6I",
        "video_title": "Inom Scania produktion: Tillverkningsprocess på Lastbilsfabriken",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d130603.48820521029!2d17.67627411091932!3d59.238085496816325!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f12baeb6eae75%3A0x16a5832b5a283d07!2zU0NBTklBIFPDtmRlcnTDpGxqZQ!5e0!3m2!1ssv!2sse!4v1749832105161!5m2!1ssv!2sse",
        "map_title": "Scania Södertälje Location",
        "detailed_description": """Scania is a leading Swedish manufacturer of commercial vehicles, buses, and industrial engines, renowned for their commitment to sustainable transport solutions and engineering excellence in the heavy-duty vehicle industry.

During my time at Scania Södertälje, I progressed from a junior technician role to a more autonomous position, developing engineering and troubleshooting expertise over two separate engagements.

**Initial Role (2012):** Started as part of the second-line support team, working alongside experienced engineers and technicians. Acquired fundamental troubleshooting skills and gained a thorough understanding of Scania's organizational structure and production processes.

**Advanced Role (2016):** Returned in a more autonomous capacity that allowed me to further develop my engineering skills. Was a part of the entire troubleshooting process from case intake to resolution and reporting results to superiors. Worked across the production chain, from manufacturing line personnel to construction engineers, while gaining valuable experience in creating documentation and establishing work routines.""",
    },
    "Finnish Defence Forces": {
        "video_url": "https://www.youtube.com/embed/AcLYbg2Jk9c?si=LFG4nBnqCZ3WRfSt",
        "video_title": "Finnish Defence Forces",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d720002.5239741812!2d22.654854775421864!3d60.10216545447512!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x468da9e761c88d0f%3A0x8809aeeec13b380b!2sNyland%20Brigade!5e0!3m2!1ssv!2sse!4v1749150985148!5m2!1ssv!2sse",
        "map_title": "Nyland Brigade Location",
        "detailed_description": """The Finnish Defence Forces (Puolustusvoimat) is Finland's military organization responsible for national defense, with Nylands Brigad being a specialized coastal defense unit that trains marine commandos for amphibious and coastal operations.

During my service with Nylands Brigad, I underwent an intensive transformation from recruit to commissioned officer, culminating in a leadership role within one of Finland's most demanding military units.

**Training and Selection:** The journey began with rigorous screening processes designed to identify candidates capable of handling the responsibilities and demands of marine commando leadership. These evaluations tested not only physical capabilities but also mental resilience, decision-making under pressure, and leadership potential in high-stress environments.

**Leadership Development:** Upon successful completion of the selection process and associated training, I was commissioned as a platoon leader and entrusted with command responsibilities. This role demanded organizational skills and stress resilience, developed through intensive military training that simulated real-world operational pressures. The experience taught me to maintain clear thinking and effective decision-making even under challenging circumstances.

**Command Responsibilities:** My duties encompassed both garrison and field operations, requiring adaptability between different operational contexts. In day-to-day garrison duties, I was responsible for the command and welfare of 150 soldiers, managing everything from training schedules to personnel development. During field operations, I led a specialized unit of 30 soldiers in tactical scenarios, where coordination and split-second decision-making were essential for mission success and personnel safety.

This experience fundamentally shaped my approach to leadership, teaching me the importance of clear communication, decisive action, and maintaining team cohesion under pressure.""",
    },
    "Södersjukhuset - SÖS": {
        "video_url": None,  # SÖS page only has a map, no video
        "video_title": None,
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d38737.84701537516!2d18.003017736901185!3d59.31780499604735!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f77ec1b565595%3A0x4f818c747249a764!2sS%C3%B6dersjukhuset!5e0!3m2!1ssv!2sse!4v1749832781009!5m2!1ssv!2sse",
        "map_title": "Södersjukhuset Location",
        "detailed_description": """Södersjukhuset is one of Stockholm's largest hospitals, providing healthcare services to the southern Stockholm region with advanced medical technology.

At Södersjukhuset's radiology department, I worked with both radiology equipment and IT systems to support clinical operations and departmental efficiency.

**System Management:** I managed the department's IT infrastructure, including PACS systems, DICOM protocols, and medical imaging equipment interfaces, ensuring systems were functional and optimized for clinical use.

**Cross-Functional Collaboration:** I worked with multidisciplinary teams including clinical staff, IT specialists, and administrative personnel to align technology implementations with operational needs.

**Security and Compliance:** I analyzed IT systems for operational efficiency and security, identifying improvement opportunities while ensuring compliance with healthcare regulations including ISO 13485.""",
    },
}


def main():
    """Populate database with detailed experience content."""
    print("Phase 8A: Populating Detailed Experience Data")
    print("=" * 60)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Update each company with detailed information
    updated_count = 0
    for company_name, details in EXPERIENCE_DETAILS.items():
        print(f"\nUpdating: {company_name}")

        # Update company record
        cursor.execute(
            """
            UPDATE companies
            SET
                video_url = ?,
                video_title = ?,
                map_url = ?,
                map_title = ?,
                detailed_description = ?
            WHERE name = ?
        """,
            (
                details["video_url"],
                details["video_title"],
                details["map_url"],
                details["map_title"],
                details["detailed_description"],
                company_name,
            ),
        )

        if cursor.rowcount > 0:
            updated_count += 1
            print("  [OK] Updated successfully")
            print(f"  - Video: {'Yes' if details['video_url'] else 'No'}")
            print(f"  - Map: {'Yes' if details['map_url'] else 'No'}")
            print(f"  - Detailed Description: {len(details['detailed_description'])} characters")
        else:
            print("  [WARN] Company not found in database")

    # Commit changes
    conn.commit()

    # Verify updates
    print(f"\n{'=' * 60}")
    print("Summary:")
    print(f"  - Total companies updated: {updated_count}/{len(EXPERIENCE_DETAILS)}")

    # Query to check results
    cursor.execute(
        """
        SELECT name,
               CASE WHEN video_url IS NOT NULL THEN 'Yes' ELSE 'No' END as has_video,
               CASE WHEN map_url IS NOT NULL THEN 'Yes' ELSE 'No' END as has_map,
               CASE WHEN detailed_description IS NOT NULL THEN 'Yes' ELSE 'No' END as has_details
        FROM companies
        WHERE name IN (?, ?, ?, ?, ?, ?)
    """,
        tuple(EXPERIENCE_DETAILS.keys()),
    )

    print("\nVerification:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: Video={row[1]}, Map={row[2]}, Details={row[3]}")

    # Close connection
    conn.close()

    print(f"\n{'=' * 60}")
    print("[OK] Database population complete!")


if __name__ == "__main__":
    main()
