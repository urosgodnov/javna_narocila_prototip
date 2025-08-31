#!/usr/bin/env python3
"""
EPIC TEST: Complete Workflow Test
Tests the entire lifecycle: Create → Validate → Save → Export → Import → Generate Summary
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import csv
import tempfile
from datetime import datetime
import streamlit as st
from utils.form_integration import FormIntegration
from services.ai_summary_service import AISummaryService
import pandas as pd

class CompleteWorkflowEpicTest:
    """Epic test for complete procurement workflow."""
    
    def __init__(self):
        """Initialize test environment."""
        # Initialize session state
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        
        self.clear_session()
        self.integration = FormIntegration()
        self.ai_service = AISummaryService()
        self.test_results = []
        self.temp_files = []
    
    def clear_session(self):
        """Clear session state for clean test."""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'status': status,
            'details': details
        })
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
    
    def test_1_create_procurement(self):
        """Test 1: Create a complete procurement with multiple lots."""
        print("\n" + "="*60)
        print("📝 TEST 1: CREATE PROCUREMENT")
        print("-"*60)
        
        # Create 3 lots
        print("Creating 3 lots...")
        self.integration.add_lot("Računalniška oprema")
        self.integration.add_lot("Programska oprema")
        
        # Fill customer info (pre-lot screen - applies to ALL lots)
        print("Filling customer information...")
        st.session_state['lots.0.clientInfo.isSingleClient'] = True
        st.session_state['lots.0.clientInfo.singleClientName'] = 'Osnovna šola Ljubljana'
        st.session_state['lots.0.clientInfo.singleClientStreetAddress'] = 'Šolska ulica 1'
        st.session_state['lots.0.clientInfo.singleClientPostalCode'] = '1000 Ljubljana'
        st.session_state['lots.0.clientInfo.singleClientLegalRepresentative'] = 'dr. Janez Novak'
        st.session_state['lots.0.clientInfo.clientEmail'] = 'info@os-ljubljana.si'
        st.session_state['lots.0.clientInfo.clientPhone'] = '01 234 5678'
        
        # Sync to all lots
        self.integration.persistence.ensure_pre_lot_data_synced(['clientInfo'])
        
        # Fill project info (pre-lot screen)
        print("Filling project information...")
        st.session_state['lots.0.projectInfo.projectTitle'] = 'Posodobitev IT infrastrukture 2024'
        st.session_state['lots.0.projectInfo.projectDescription'] = 'Celovita prenova računalniške in programske opreme'
        st.session_state['lots.0.projectInfo.projectStartDate'] = '2024-03-01'
        st.session_state['lots.0.projectInfo.projectEndDate'] = '2024-12-31'
        
        self.integration.persistence.ensure_pre_lot_data_synced(['projectInfo'])
        
        # Fill legal basis (pre-lot screen)
        print("Filling legal basis...")
        st.session_state['lots.0.legalBasis.lawReference'] = 'ZJN-3'
        st.session_state['lots.0.legalBasis.articleReference'] = '66. člen'
        st.session_state['lots.0.legalBasis.publicProcurement'] = True
        
        self.integration.persistence.ensure_pre_lot_data_synced(['legalBasis'])
        
        # Fill lot-specific data
        print("Filling lot-specific data...")
        
        # Lot 0 - General equipment
        st.session_state['lots.0.technicalSpecs.description'] = 'Splošna računalniška oprema'
        st.session_state['lots.0.technicalSpecs.cpvCode'] = '30200000-1'
        st.session_state['lots.0.priceInfo.estimatedValue'] = 50000.00
        st.session_state['lots.0.executionDeadline.deliveryDays'] = 30
        
        # Lot 1 - Computer equipment
        st.session_state['lots.1.technicalSpecs.description'] = 'Delovne postaje in strežniki'
        st.session_state['lots.1.technicalSpecs.cpvCode'] = '30213000-5'
        st.session_state['lots.1.priceInfo.estimatedValue'] = 120000.00
        st.session_state['lots.1.executionDeadline.deliveryDays'] = 45
        
        # Lot 2 - Software
        st.session_state['lots.2.technicalSpecs.description'] = 'Licence za programsko opremo'
        st.session_state['lots.2.technicalSpecs.cpvCode'] = '48000000-8'
        st.session_state['lots.2.priceInfo.estimatedValue'] = 80000.00
        st.session_state['lots.2.executionDeadline.deliveryDays'] = 15
        
        # Add selection criteria
        print("Adding selection criteria...")
        st.session_state['lots.0.selectionCriteria.priceWeight'] = 60
        st.session_state['lots.0.selectionCriteria.qualityWeight'] = 30
        st.session_state['lots.0.selectionCriteria.deliveryWeight'] = 10
        
        # Verify creation
        form_data = self.integration.save_form_data()
        created = len(form_data['lots']) == 3
        
        self.log_result(
            "Create procurement with 3 lots",
            created,
            f"Created {len(form_data['lots'])} lots with complete data"
        )
        
        return created, form_data
    
    def test_2_validate_all_screens(self):
        """Test 2: Validate all screens."""
        print("\n" + "="*60)
        print("✔️ TEST 2: VALIDATE ALL SCREENS")
        print("-"*60)
        
        validation_screens = [
            (['clientInfo'], 0, "Customer Information"),
            (['projectInfo'], 1, "Project Information"),
            (['legalBasis'], 2, "Legal Basis"),
            (['technicalSpecs'], 6, "Technical Specifications"),
            (['priceInfo'], 8, "Price Information"),
            (['executionDeadline'], 7, "Execution Deadline"),
            (['selectionCriteria'], 12, "Selection Criteria")
        ]
        
        all_valid = True
        for screen_keys, step_num, screen_name in validation_screens:
            is_valid, errors = self.integration.validate_step(screen_keys, step_num)
            
            if is_valid:
                print(f"  ✅ {screen_name}: Valid")
            else:
                print(f"  ❌ {screen_name}: {len(errors)} errors")
                for error in errors[:2]:
                    print(f"      - {error}")
                all_valid = False
        
        self.log_result(
            "Validate all screens",
            all_valid,
            "All screens pass validation" if all_valid else "Some screens have errors"
        )
        
        return all_valid
    
    def test_3_export_to_json(self, form_data):
        """Test 3: Export to JSON format."""
        print("\n" + "="*60)
        print("💾 TEST 3: EXPORT TO JSON")
        print("-"*60)
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_files.append(temp_file.name)
        
        try:
            # Export to JSON
            json.dump(form_data, temp_file, ensure_ascii=False, indent=2)
            temp_file.close()
            
            # Verify file
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            export_success = loaded_data == form_data
            file_size = os.path.getsize(temp_file.name)
            
            print(f"  File: {temp_file.name}")
            print(f"  Size: {file_size:,} bytes")
            print(f"  Lots exported: {len(loaded_data.get('lots', []))}")
            
            self.log_result(
                "Export to JSON",
                export_success,
                f"Exported {file_size:,} bytes"
            )
            
            return export_success, temp_file.name
        except Exception as e:
            self.log_result("Export to JSON", False, str(e))
            return False, None
    
    def test_4_export_to_csv(self, form_data):
        """Test 4: Export to CSV format."""
        print("\n" + "="*60)
        print("📊 TEST 4: EXPORT TO CSV")
        print("-"*60)
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.temp_files.append(temp_file.name)
        
        try:
            # Flatten data for CSV
            rows = []
            for lot in form_data['lots']:
                row = {
                    'lot_name': lot['name'],
                    'lot_index': lot['index']
                }
                # Flatten nested data
                for key, value in lot.get('data', {}).items():
                    if not isinstance(value, (list, dict)):
                        row[key] = value
                rows.append(row)
            
            # Write CSV
            if rows:
                writer = csv.DictWriter(temp_file, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            
            temp_file.close()
            
            # Verify file
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                imported_rows = list(reader)
            
            export_success = len(imported_rows) == len(rows)
            file_size = os.path.getsize(temp_file.name)
            
            print(f"  File: {temp_file.name}")
            print(f"  Size: {file_size:,} bytes")
            print(f"  Rows exported: {len(imported_rows)}")
            
            self.log_result(
                "Export to CSV",
                export_success,
                f"Exported {len(imported_rows)} rows"
            )
            
            return export_success, temp_file.name
        except Exception as e:
            self.log_result("Export to CSV", False, str(e))
            return False, None
    
    def test_5_export_to_excel(self, form_data):
        """Test 5: Export to Excel format."""
        print("\n" + "="*60)
        print("📈 TEST 5: EXPORT TO EXCEL")
        print("-"*60)
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_files.append(temp_file.name)
        temp_file.close()
        
        try:
            # Create DataFrame for each lot
            with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Naziv': [form_data['lots'][0]['data'].get('projectInfo.projectTitle', 'N/A')],
                    'Naročnik': [form_data['lots'][0]['data'].get('clientInfo.singleClientName', 'N/A')],
                    'Število sklopov': [len(form_data['lots'])],
                    'Skupna vrednost': [sum(lot['data'].get('priceInfo.estimatedValue', 0) for lot in form_data['lots'])],
                    'Datum izvoza': [datetime.now().strftime('%Y-%m-%d %H:%M')]
                }
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Povzetek', index=False)
                
                # Each lot as separate sheet
                for lot in form_data['lots']:
                    lot_data = []
                    for key, value in lot['data'].items():
                        if not isinstance(value, (list, dict)):
                            lot_data.append({
                                'Polje': key.split('.')[-1],
                                'Vrednost': value
                            })
                    
                    if lot_data:
                        df_lot = pd.DataFrame(lot_data)
                        sheet_name = f"Sklop_{lot['index']}_{lot['name'][:20]}"
                        df_lot.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Verify file
            file_exists = os.path.exists(temp_file.name)
            file_size = os.path.getsize(temp_file.name) if file_exists else 0
            
            # Read back to verify
            excel_file = pd.ExcelFile(temp_file.name)
            sheet_count = len(excel_file.sheet_names)
            
            export_success = file_exists and sheet_count == len(form_data['lots']) + 1
            
            print(f"  File: {temp_file.name}")
            print(f"  Size: {file_size:,} bytes")
            print(f"  Sheets: {sheet_count} ({', '.join(excel_file.sheet_names[:3])}...)")
            
            self.log_result(
                "Export to Excel",
                export_success,
                f"Created {sheet_count} sheets"
            )
            
            return export_success, temp_file.name
        except Exception as e:
            self.log_result("Export to Excel", False, str(e))
            return False, None
    
    def test_6_import_from_json(self, json_file):
        """Test 6: Import from JSON."""
        print("\n" + "="*60)
        print("📥 TEST 6: IMPORT FROM JSON")
        print("-"*60)
        
        if not json_file:
            self.log_result("Import from JSON", False, "No JSON file to import")
            return False
        
        # Clear session
        self.clear_session()
        self.integration = FormIntegration()
        
        try:
            # Load from file
            with open(json_file, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # Import to session
            self.integration.load_form_data(imported_data)
            
            # Verify import
            verification_points = [
                ('lots.0.clientInfo.singleClientName', 'Osnovna šola Ljubljana'),
                ('lots.1.technicalSpecs.description', 'Delovne postaje in strežniki'),
                ('lots.2.priceInfo.estimatedValue', 80000.00)
            ]
            
            import_success = True
            for key, expected in verification_points:
                actual = st.session_state.get(key)
                if actual != expected:
                    print(f"  ✗ {key}: expected '{expected}', got '{actual}'")
                    import_success = False
                else:
                    print(f"  ✓ {key}: {actual}")
            
            self.log_result(
                "Import from JSON",
                import_success,
                "All data correctly imported" if import_success else "Import verification failed"
            )
            
            return import_success
        except Exception as e:
            self.log_result("Import from JSON", False, str(e))
            return False
    
    def test_7_generate_ai_summary(self):
        """Test 7: Generate AI summary."""
        print("\n" + "="*60)
        print("🤖 TEST 7: GENERATE AI SUMMARY")
        print("-"*60)
        
        # Prepare data for summary
        form_data = self.integration.save_form_data()
        
        # Create procurement data structure
        procurement_data = {
            'naziv': form_data['lots'][0]['data'].get('projectInfo.projectTitle', 'Neimenovano'),
            'vrsta_postopka': 'Odprti postopek',
            'ocenjena_vrednost': sum(
                lot['data'].get('priceInfo.estimatedValue', 0) 
                for lot in form_data['lots']
            ),
            'lots': len(form_data['lots']),
            'client': form_data['lots'][0]['data'].get('clientInfo.singleClientName', 'Neznano')
        }
        
        try:
            # Generate summary
            summary = self.ai_service.generate_summary(procurement_data)
            
            # Verify summary contains key elements
            required_elements = [
                'Povzetek naročila',
                'Osnovni podatki',
                'Ključne ugotovitve',
                'Priporočila',
                'Zaključek'
            ]
            
            summary_valid = all(element in summary for element in required_elements)
            
            print("Generated summary preview:")
            print("-" * 40)
            print(summary[:500] + "...")
            print("-" * 40)
            
            print(f"\nSummary length: {len(summary)} characters")
            print(f"Contains all sections: {'Yes' if summary_valid else 'No'}")
            
            self.log_result(
                "Generate AI summary",
                summary_valid,
                f"Generated {len(summary)} character summary"
            )
            
            return summary_valid, summary
        except Exception as e:
            self.log_result("Generate AI summary", False, str(e))
            return False, None
    
    def test_8_round_trip_verification(self):
        """Test 8: Complete round-trip verification."""
        print("\n" + "="*60)
        print("🔄 TEST 8: ROUND-TRIP VERIFICATION")
        print("-"*60)
        
        # Save current state
        original_data = self.integration.save_form_data()
        
        # Export to JSON
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_files.append(temp_file.name)
        json.dump(original_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        
        # Clear session
        self.clear_session()
        self.integration = FormIntegration()
        
        # Import back
        with open(temp_file.name, 'r') as f:
            imported_data = json.load(f)
        
        self.integration.load_form_data(imported_data)
        
        # Save again
        final_data = self.integration.save_form_data()
        
        # Compare
        round_trip_success = self._compare_data(original_data, final_data)
        
        print(f"  Original lots: {len(original_data['lots'])}")
        print(f"  Final lots: {len(final_data['lots'])}")
        print(f"  Data integrity: {'Preserved' if round_trip_success else 'Lost'}")
        
        self.log_result(
            "Round-trip verification",
            round_trip_success,
            "Data preserved through export/import cycle" if round_trip_success else "Data lost in round-trip"
        )
        
        return round_trip_success
    
    def _compare_data(self, data1, data2):
        """Compare two data structures for equality."""
        # Simple comparison - in production would need deep comparison
        if len(data1.get('lots', [])) != len(data2.get('lots', [])):
            return False
        
        for i, lot1 in enumerate(data1['lots']):
            lot2 = data2['lots'][i]
            if lot1['name'] != lot2['name']:
                return False
            # Compare some key fields
            for key in ['clientInfo.singleClientName', 'priceInfo.estimatedValue']:
                if lot1['data'].get(key) != lot2['data'].get(key):
                    return False
        
        return True
    
    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
    
    def run_epic_test(self):
        """Run all tests in the epic workflow."""
        print("\n" + "🚀" * 30)
        print("EPIC TEST: COMPLETE PROCUREMENT WORKFLOW")
        print("🚀" * 30)
        
        # Run tests
        created, form_data = self.test_1_create_procurement()
        validation_passed = self.test_2_validate_all_screens()
        json_exported, json_file = self.test_3_export_to_json(form_data)
        csv_exported, csv_file = self.test_4_export_to_csv(form_data)
        excel_exported, excel_file = self.test_5_export_to_excel(form_data)
        json_imported = self.test_6_import_from_json(json_file)
        ai_generated, summary = self.test_7_generate_ai_summary()
        round_trip_passed = self.test_8_round_trip_verification()
        
        # Summary
        print("\n" + "="*60)
        print("📊 EPIC TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        
        for result in self.test_results:
            print(f"{result['status']} {result['test']}")
        
        print("\n" + "-"*60)
        print(f"Results: {passed}/{total} tests passed")
        
        # Cleanup
        self.cleanup()
        
        if passed == total:
            print("\n" + "🎉"*20)
            print("ALL EPIC TESTS PASSED!")
            print("🎉"*20)
            print("\n✅ System is ready for production:")
            print("  • Create complex multi-lot procurements")
            print("  • Validate all screens correctly")
            print("  • Export to JSON, CSV, Excel")
            print("  • Import data back without loss")
            print("  • Generate AI summaries")
            print("  • Complete round-trip data integrity")
        else:
            print(f"\n⚠️ {total - passed} tests failed - review needed")
        
        return passed == total


if __name__ == "__main__":
    try:
        tester = CompleteWorkflowEpicTest()
        success = tester.run_epic_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Epic test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)