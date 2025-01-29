# const.py
DOMAIN = "infpro" 
UPDATE_INTERVAL = 180  # Intervalul implicit de actualizare (în secunde)
DEFAULT_ORAS = "5"  # Orașul implicit (Alba Iulia), din LISTA_ORASE

PLATFORMS = ["sensor"]


# URL-urile pentru API
BASE_URL = "https://dev.syspro.ro"
URL_CUTREMUR = f"{BASE_URL}/homeassistant/date_api.json"

# Lista codurilor de județe
LISTA_JUDET = [
    "AB", "AR", "AG", "BC", "BH", "BN", "BR", "BT", "BV", "BZ",
    "CS", "CL", "CJ", "CT", "CV", "DB", "DJ", "GL", "GR", "GJ",
    "HR", "HD", "IL", "IS", "IF", "MM", "MH", "MS", "NT", "OT",
    "PH", "SM", "SJ", "SB", "SV", "TR", "TM", "TL", "VS", "VL",
    "VN", "B"
]

# Dicționar compact pentru coduri și numele complete ale județelor
JUDETE_MAP = {
    "AB": "Alba", "AR": "Arad", "AG": "Argeș", "BC": "Bacău", "BH": "Bihor",
    "BN": "Bistrița-Năsăud", "BR": "Brăila", "BT": "Botoșani", "BV": "Brașov", "BZ": "Buzău",
    "CS": "Caraș-Severin", "CL": "Călărași", "CJ": "Cluj", "CT": "Constanța", "CV": "Covasna",
    "DB": "Dâmbovița", "DJ": "Dolj", "GL": "Galați", "GR": "Giurgiu", "GJ": "Gorj",
    "HR": "Harghita", "HD": "Hunedoara", "IL": "Ialomița", "IS": "Iași", "IF": "Ilfov",
    "MM": "Maramureș", "MH": "Mehedinți", "MS": "Mureș", "NT": "Neamț", "OT": "Olt",
    "PH": "Prahova", "SM": "Satu Mare", "SJ": "Sălaj", "SB": "Sibiu", "SV": "Suceava",
    "TR": "Teleorman", "TM": "Timiș", "TL": "Tulcea", "VS": "Vaslui", "VL": "Vâlcea",
    "VN": "Vrancea", "B": "București"
}

LISTA_ORASE = [
    "1: Abrud", "2: Adjud", "3: Agnita", "4: Aiud", "5: Alba Iulia",
    "6: Albesti", "7: Alesd", "8: Alexandria", "9: Amara", "10: Anina",
    "11: Aninoasa", "12: Arad", "13: Ardud", "14: Avrig", "15: Azuga",
    "16: Babadag", "17: Babeni", "18: Bacau", "19: Baia De Arama", "20: Baia De Aries",
    "21: Baia Mare", "22: Baia Sprie", "23: Baicoi", "24: Baile Herculane", "25: Baile Olanesti",
    "26: Baile Tusnad", "27: Bailesti", "28: Balan", "29: Bals", "30: Baneasa",
    "31: Baraolt", "32: Barlad", "33: Basarabi", "34: Bechet", "35: Beclean",
    "36: Beius", "37: Berbesti", "38: Beresti", "39: Bicaz", "40: Bistrita",
    "41: Blaj", "42: Bocsa", "43: Boldesti-Scaeni", "44: Bolintin-Vale", "45: Borsa",
    "46: Borsec", "47: Botosani", "48: Brad", "49: Bragadiru", "50: Braila",
    "51: Brasov", "52: Brezoi", "53: Brosteni", "54: Bucecea", "55: Bucuresti",
    "56: Budesti", "57: Buftea", "58: Buhusi", "59: Bumbesti-Jiu", "60: Busteni",
    "61: Buzau", "62: Buzias", "63: Cajvana", "64: Calafat", "65: Calarasi",
    "66: Calimanesti-Caciulata", "67: Campeni", "68: Campia Turzii", "69: Campina", "70: Campulung",
    "71: Campulung Moldovenesc", "72: Caracal", "73: Caransebes", "74: Carei", "75: Cavnic",
    "76: Cazanesti", "77: Cehu Silvaniei", "78: Cernavoda", "79: Chisineu-Cris", "80: Chitila",
    "81: Ciacova", "82: Cisnadie", "83: Cluj-Napoca", "84: Codlea", "85: Comanesti",
    "86: Comarnic", "87: Constanta", "88: Copsa Mica", "89: Corabia", "90: Costesti",
    "91: Covasna", "92: Craiova", "93: Cristuru Secuiesc", "94: Cugir", "95: Curtea De Arges",
    "96: Curtici", "97: Dabuleni", "98: Darmanesti", "99: Dej", "100: Deta",
    "101: Deva", "102: Dolhasca", "103: Dorohoi", "104: Draganesti-Olt", "105: Dragasani",
    "106: Dragomiresti", "107: Drobeta-Turnu Severin", "108: Dumbraveni", "109: Fagaras", "110: Faget",
    "111: Falticeni", "112: Faurei", "113: Fetesti", "114: Fieni", "115: Fierbinti-Targ",
    "116: Filiasi", "117: Flamanzi", "118: Focsani", "119: Frasin", "120: Fundulea",
    "121: Gaesti", "122: Galati", "123: Gataia", "124: Geoagiu", "125: Gheorgheni",
    "126: Gherla", "127: Ghimbav", "128: Giurgiu", "129: Gura Humorului", "130: Harlau",
    "131: Harsova", "132: Hateg", "133: Horezu", "134: Huedin", "135: Hunedoara",
    "136: Ianca", "137: Iasi", "138: Iernut", "139: Ineu", "140: Insuratei",
    "141: Intorsura Buzaului", "142: Isaccea", "143: Jibou", "144: Jimbolia", "145: Lehliu-Gara",
    "146: Lipova", "147: Liteni", "148: Livada", "149: Ludus", "150: Lugoj",
    "151: Lupeni-Hr", "152: Lupeni-Hu", "153: Macin", "154: Magurele", "155: Mangalia",
    "156: Marasesti", "157: Marghita", "158: Medgidia", "159: Medias", "160: Miercurea Ciuc",
    "161: Miercurea Nirajului", "162: Miercurea Sibiului", "163: Mihailesti", "164: Milisauti", "165: Mioveni",
    "166: Mizil", "167: Moinesti", "168: Moldova Noua", "169: Moreni", "170: Motru",
    "171: Murgeni", "172: Nadlac", "173: Nasaud", "174: Navodari", "175: Negresti",
    "176: Negresti-Oas", "177: Negru Voda", "178: Nehoiu", "179: Novaci", "180: Nucet",
    "181: Ocna Mures", "182: Ocna Sibiului", "183: Ocnele Mari", "184: Odobesti", "185: Odorheiu Secuiesc",
    "186: Oltenita", "187: Onesti", "188: Oradea", "189: Orastie", "190: Oravita",
    "191: Orsova", "192: Otelu Rosu", "193: Otopeni", "194: Ovidiu", "195: Panciu",
    "196: Pancota", "197: Pantelimon", "198: Pascani", "199: Patarlagele", "200: Pecica",
    "201: Petrila", "202: Petrosani", "203: Piatra Neamt", "204: Piatra Olt", "205: Pitesti",
    "206: Ploiesti", "207: Plopeni", "208: Pogoanele", "209: Potcoava", "210: Predeal",
    "211: Pucioasa", "212: Racari", "213: Radauti", "214: Ramnicu Sarat", "215: Ramnicu Valcea",
    "216: Rasnov", "217: Recas", "218: Reghin", "219: Resita", "220: Roman",
    "221: Rosiori De Vede", "222: Rovinari", "223: Roznov", "224: Rupea", "225: Sacele",
    "226: Salcea", "227: Saliste", "228: Salistea De Sus", "229: Salonta", "230: Sangeorgiu De Mures",
    "231: Sangeorgiu De Padure", "232: Sannicolau Mare", "233: Santana", "234: Sarmasu", "235: Satu Mare",
    "236: Saveni", "237: Scornicesti", "238: Sebes", "239: Sebis", "240: Segarcea",
    "241: Seini", "242: Sfantu Gheorghe", "243: Sibiu", "244: Sighetu Marmatiei", "245: Sighisoara",
    "246: Simeria", "247: Simleu Silvaniei", "248: Sinaia", "249: Siret", "250: Slanic",
    "251: Slanic-Moldova", "252: Slatina", "253: Slobozia", "254: Solca", "255: Somcuta Mare",
    "256: Sovata", "257: Stefanesti-Bt", "258: Stefanesti-Ag", "259: Stei", "260: Strehaia",
    "261: Suceava", "262: Talmaciu", "263: Tandarei", "264: Targoviste", "265: Targu Bujor",
    "266: Targu Carbunesti", "267: Targu Frumos", "268: Targu Jiu", "269: Targu Lapus", "270: Targu Mures",
    "271: Targu Ocna", "272: Targu Secuiesc", "273: Targu-Neamt", "274: Tarnaveni", "275: Tasnad",
    "276: Tautii-Magheraus", "277: Techirghiol", "278: Tecuci", "279: Teius", "280: Ticleni",
    "281: Timisoara", "282: Tismana", "283: Titu", "284: Toplita", "285: Topoloveni",
    "286: Tulcea", "287: Turceni", "288: Turda", "289: Turnu Magurele", "290: Ulmeni",
    "291: Ungheni", "292: Uricani", "293: Urziceni", "294: Valea Lui Mihai", "295: Valenii De Munte",
    "296: Vanju Mare", "297: Vascau", "298: Vaslui", "299: Vatra Dornei", "300: Vicovu De Jos",
    "301: Vicovu De Sus", "302: Victoria", "303: Videle", "304: Viseu De Sus", "305: Vlahita",
    "306: Voluntari", "307: Vulcan", "308: Zalau", "309: Zarnesti", "310: Zimnicea", "311: Zlatna"
]

INTENSITY_MAP = {
    "I": "Neresimțită", "I-II": "Neresimțită Slabă", "II": "Slabă", "III": "Slabă",
    "IV": "Ușoară", "V": "Moderată", "VI": "Puternică", "VII": "Foarte puternică",
    "VIII": "Severă", "IX": "Violentă", "X": "Extremă", "XI": "Catastrofală", "XII": "Apocaliptică"
}

ATTRIBUTION = "Date furnizate de Institutul Național de Cercetare și Dezvoltare pentru Fizica Pământului"
