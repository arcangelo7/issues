#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2022, Arcangelo Massari <arcangelo.massari@unibo.it>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.


from process_issues import *
import unittest


VALID_BODY = """
"id","title","author","pub_date","venue","volume","issue","page","type","publisher","editor"
"doi:10.1007/978-3-662-07918-8_3","Influence of Dielectric Properties, State, and Electrodes on Electric Strength","Ushakov, Vasily Y.","2004","Insulation of High-Voltage Equipment [isbn:9783642058530 isbn:9783662079188]","","","27-82","book chapter","Springer Science and Business Media LLC [crossref:297]",""
"doi:10.1016/0021-9991(73)90147-2","Flux-corrected transport. I. SHASTA, a fluid transport algorithm that works","Boris, Jay P; Book, David L","1973-1","Journal of Computational Physics [issn:0021-9991]","11","1","38-69","journal article","Elsevier BV [crossref:78]",""
"doi:10.1109/20.877674","An investigation of FEM-FCT method for streamer corona simulation","Woong-Gee Min, ; Hyeong-Seok Kim, ; Seok-Hyun Lee, ; Song-Yop Hahn, ","2000-7","IEEE Transactions on Magnetics [issn:0018-9464]","36","4","1280-1284","journal article","Institute of Electrical and Electronics Engineers (IEEE) [crossref:263]",""
"doi:10.1109/tps.2003.815469","Numerical study on influences of barrier arrangements on dielectric barrier discharge characteristics","Woo Seok Kang, ; Jin Myung Park, ; Yongho Kim, ; Sang Hee Hong, ","2003-8","IEEE Transactions on Plasma Science [issn:0093-3813]","31","4","504-510","journal article","Institute of Electrical and Electronics Engineers (IEEE) [crossref:263]",""
"","Spatial Distribution of Ion Current Around HVDC Bundle Conductors","Zhou, Xiangxian; Cui, Xiang; Lu, Tiebing; Fang, Chao; Zhen, Yongzan","2012-1","IEEE Transactions on Power Delivery [issn:0885-8977 issn:1937-4208]","27","1","380-390","journal article","Institute of Electrical and Electronics Engineers (IEEE) [crossref:263]",""
"doi:10.1007/978-1-4615-3786-1_11","The Solution of the Continuity Equations in Ionization and Plasma Growth","Davies, A. J.; Niessen, W.","1990","Physics and Applications of Pseudosparks [isbn:9781461366874 isbn:9781461537861]","","","197-217","book chapter","Springer Science and Business Media LLC [crossref:297]",""
"doi:10.1088/0022-3727/13/1/002","Discharge current induced by the motion of charged particles","Sato, N","1980-1-14","Journal of Physics D: Applied Physics [issn:0022-3727 issn:1361-6463]","13","1","3-6","journal article","IOP Publishing [crossref:266]",""
"doi:10.1109/27.106800","Particle-in-cell charged-particle simulations, plus Monte Carlo collisions with neutral atoms, PIC-MCC","Birdsall, C.K.","1991-4","IEEE Transactions on Plasma Science [issn:0093-3813]","19","2","65-85","journal article","Institute of Electrical and Electronics Engineers (IEEE) [crossref:263]",""
"doi:10.1016/0021-9991(79)90051-2","Fully multidimensional flux-corrected transport algorithms for fluids","Zalesak, Steven T","1979-6","Journal of Computational Physics [issn:0021-9991]","31","3","335-362","journal article","Elsevier BV [crossref:78]",""
"doi:10.1088/0022-3727/39/14/017","Diffusion correction to the Raether–Meek criterion for the avalanche-to-streamer transition","Montijn, Carolynne; Ebert, Ute [orcid:0000-0003-3891-6869]","2006-6-30","Journal of Physics D: Applied Physics [issn:0022-3727 issn:1361-6463]","39","14","2979-2992","journal article","IOP Publishing [crossref:266]",""
"doi:10.1007/978-3-663-14090-0 isbn:9783528085995 isbn:9783663140900","High-Voltage Insulation Technology","Kind, Dieter; Kärner, Hermann","1985","","","","","book","Springer Science and Business Media LLC [crossref:297]",""
"","Space-charge effects in high-density plasmas","Morrow, R","1982-6","Journal of Computational Physics [issn:0021-9991]","46","3","454-461","journal article","Elsevier BV [crossref:78]",""
"doi:10.1007/s42835-022-01029-y","Numerical Simulation of Gas Discharge Using SUPG-FEM-FCT Method with Adaptive Mesh Refinement","Choi, Chan Young; Park, Il Han [orcid:0000-0002-9383-6856]","2022-2-28","Journal of Electrical Engineering & Technology [issn:1975-0102 issn:2093-7423]","17","3","1873-1881","journal article","Springer Science and Business Media LLC [crossref:297]",""
===###===@@@===
"citing_id","citing_publication_date","cited_id","cited_publication_date"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1007/978-3-662-07918-8_3","2004"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1016/0021-9991(73)90147-2","1973-1"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1109/20.877674","2000-7"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1109/tps.2003.815469",""
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1109/tpwrd.2011.2172694","2012-1"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1007/978-1-4615-3786-1_11","1990"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1088/0022-3727/13/1/002","1980-1-14"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1109/27.106800","1991-4"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1016/0021-9991(79)90051-2","1979-6"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1088/0022-3727/39/14/017",""
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1007/978-3-663-14090-0","1985"
"doi:10.1007/s42835-022-01029-y","2022-02-28","doi:10.1016/0021-9991(82)90026-2",""
"""


class Test_process_issues(unittest.TestCase):
    def test_valid_title_and_body(self):
        issue_title = "deposit localhost:330 doi:10.1007/s42835-022-01029-y"
        issue_body = VALID_BODY
        is_valid, message = validate(issue_title, issue_body)
        expected_message = 'Thank you for your contribution! OpenCitations will process the data you provided within a week. Afterwards, citations will be available through the [CROCI](https://opencitations.net/index/croci) index and metadata through OpenCitations Meta'
        self.assertEqual((is_valid, message), (True, expected_message))

    def test_title_no_supported_schema(self):
        issue_title = "deposit localhost:330 pippo:10.1007/s42835-022-01029-y"
        issue_body = VALID_BODY
        is_valid, message = validate(issue_title, issue_body)
        expected_message = 'The title of the issue was not structured correctly. Please, follow this format: deposit {domain name of journal} {doi or other supported identifier}. For example "deposit localhost:330 doi:10.1007/978-3-030-00668-6_8". The following identifiers are currently supported: doi, issn, isbn, pmid, pmcid, url, wikidata, and wikipedia'
        self.assertEqual((is_valid, message), (False, expected_message))

    def test_title_no_deposit_keyword(self):
        issue_title = "deposits localhost:330 doi:10.1007/s42835-022-01029-y"
        issue_body = VALID_BODY
        is_valid, message = validate(issue_title, issue_body)
        expected_message = 'The title of the issue was not structured correctly. Please, follow this format: deposit {domain name of journal} {doi or other supported identifier}. For example "deposit localhost:330 doi:10.1007/978-3-030-00668-6_8". The following identifiers are currently supported: doi, issn, isbn, pmid, pmcid, url, wikidata, and wikipedia'
        self.assertEqual((is_valid, message), (False, expected_message))

    def test_title_invalid_id(self):
        issue_title = "deposit localhost:330 doi:10.1007/s42835-022-01029-y."
        issue_body = VALID_BODY
        is_valid, message = validate(issue_title, issue_body)
        expected_message = "The identifier with literal value 10.1007/s42835-022-01029-y. specified in the issue title is not a valid DOI"
        self.assertEqual((is_valid, message), (False, expected_message))
    
    def test_body_no_sep(self):
        issue_title = "deposit localhost:330 doi:10.1007/s42835-022-01029-y"
        issue_body = VALID_BODY.replace("===###===@@@===", "")
        is_valid, message = validate(issue_title, issue_body)
        expected_message = 'Please use the separator "===###===@@@===" to divide metadata from citations, as shown in the following guide: https://github.com/arcangelo7/issues/blob/main/README.md'
        self.assertEqual((is_valid, message), (False, expected_message))

    def test_body_invalid_csv(self):
        issue_title = "deposit localhost:330 doi:10.1007/s42835-022-01029-y"
        issue_body = VALID_BODY + ",,,,,"
        is_valid, message = validate(issue_title, issue_body)
        expected_message = 'The data you provided could not be processed as a CSV. Please, check that the metadata CSV and the citation CSV are valid CSVs'
        self.assertEqual((is_valid, message), (False, expected_message))


if __name__ == '__main__':
    unittest.main()