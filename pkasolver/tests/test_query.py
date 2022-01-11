from rdkit import Chem
from pkasolver.query import calculate_microstate_pka_values, _get_ionization_indices
import numpy as np

input = "pkasolver/tests/testdata/00_chembl_subset.sdf"
mollist = []
with open(input, "rb") as fh:
    suppl = Chem.ForwardSDMolSupplier(fh, removeHs=True)
    for i, mol in enumerate(suppl):
        mollist.append(mol)


def test_generate_query():
    from pkasolver.query import QueryModel
    import pickle

    q = QueryModel()
    pickle.dump(q, open("pkasolver/trained_model/trained_model.pickle", "wb"))


def test_predict():
    from pkasolver.data import (
        make_features_dicts,
        mol_to_paired_mol_data,
    )
    from pkasolver.ml import dataset_to_dataloader, predict_pka_value
    from pkasolver.constants import EDGE_FEATURES, NODE_FEATURES
    from pkasolver.query import QueryModel

    node_feat_list = [
        "element",
        "formal_charge",
        "hybridization",
        "total_num_Hs",
        "aromatic_tag",
        "total_valence",
        "total_degree",
        "is_in_ring",
        "reaction_center",
        "smarts",
    ]

    edge_feat_list = ["bond_type", "is_conjugated", "rotatable"]
    query_model = QueryModel()

    # make dicts from selection list to be used in the processing step
    selected_node_features = make_features_dicts(NODE_FEATURES, node_feat_list)
    selected_edge_features = make_features_dicts(EDGE_FEATURES, edge_feat_list)
    prot = Chem.MolFromSmiles(
        "Nc1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc([NH3+])c5ccccc54)c3)c2)c2ccccc12"
    )
    deprot = Chem.MolFromSmiles(
        "Nc1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc(N)c5ccccc54)c3)c2)c2ccccc12"
    )
    m = mol_to_paired_mol_data(
        prot, deprot, 21, selected_node_features, selected_edge_features,
    )
    loader = dataset_to_dataloader([m], 1, shuffle=False)
    assert np.isclose(predict_pka_value(query_model.model, loader), 2.39621401)

    deprot = Chem.MolFromSmiles(
        "[NH-]c1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc(N)c5ccccc54)c3)c2)c2ccccc12"
    )
    prot = Chem.MolFromSmiles(
        "Nc1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc(N)c5ccccc54)c3)c2)c2ccccc12"
    )
    m = mol_to_paired_mol_data(
        prot, deprot, 0, selected_node_features, selected_edge_features,
    )
    loader = dataset_to_dataloader([m], 1, shuffle=False)
    assert np.isclose(predict_pka_value(query_model.model, loader), 11.28736687)

    # https://en.wikipedia.org/wiki/Acetic_acid
    deprot = Chem.MolFromSmiles("CC(=O)[O-]")
    prot = Chem.MolFromSmiles("CC(=O)O")

    idx = _get_ionization_indices([deprot, prot], prot)[0]
    m = mol_to_paired_mol_data(
        prot, deprot, idx, selected_node_features, selected_edge_features,
    )
    loader = dataset_to_dataloader([m], 1, shuffle=False)
    assert np.isclose(predict_pka_value(query_model.model, loader), 4.81062174)
    # https://www.masterorganicchemistry.com/2017/04/18/basicity-of-amines-and-pkah/
    deprot = Chem.MolFromSmiles("c1ccncc1")
    prot = Chem.MolFromSmiles("c1cc[nH+]cc1")
    idx = _get_ionization_indices([deprot, prot], prot)[0]
    m = mol_to_paired_mol_data(
        prot, deprot, idx, selected_node_features, selected_edge_features,
    )
    loader = dataset_to_dataloader([m], 1, shuffle=False)
    assert np.isclose(predict_pka_value(query_model.model, loader), 5.32189131)

    # https://www.masterorganicchemistry.com/2017/04/18/basicity-of-amines-and-pkah/
    deprot = Chem.MolFromSmiles("C1CCNCC1")
    prot = Chem.MolFromSmiles("C1CC[NH2+]CC1")
    idx = _get_ionization_indices([deprot, prot], prot)[0]
    m = mol_to_paired_mol_data(
        prot, deprot, idx, selected_node_features, selected_edge_features,
    )
    loader = dataset_to_dataloader([m], 1, shuffle=False)
    assert np.isclose(predict_pka_value(query_model.model, loader), 11.02899933)


def test_piperidine():
    # https://www.masterorganicchemistry.com/2017/04/18/basicity-of-amines-and-pkah/
    mol = Chem.MolFromSmiles("C1CCNCC1")
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=True)
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "C1CC[NH2+]CC1"
    assert Chem.MolToSmiles(pair[1]) == "C1CCNCC1"
    assert np.isclose(pka, 11.02899933)
    assert idx == 3

    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    assert len(molpairs) == 1
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "C1CC[NH2+]CC1"
    assert Chem.MolToSmiles(pair[1]) == "C1CCNCC1"
    assert np.isclose(pka, 11.02899933)
    assert idx == 3


def test_pyridine():
    # https://www.masterorganicchemistry.com/2017/04/18/basicity-of-amines-and-pkah/
    mol = Chem.MolFromSmiles("C1=CC=NC=C1")
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=True)
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "c1cc[nH+]cc1"
    assert Chem.MolToSmiles(pair[1]) == "c1ccncc1"
    assert np.isclose(pka, 5.32189131)
    assert idx == 3


def test_acetic_acid():
    # https://en.wikipedia.org/wiki/Acetic_acid
    mol = Chem.MolFromSmiles("CC(=O)[O-]")
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "CC(=O)O"
    assert Chem.MolToSmiles(pair[1]) == "CC(=O)[O-]"
    assert np.isclose(pka, 4.81062174)
    assert idx == 3

    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=True)
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "CC(=O)O"
    assert Chem.MolToSmiles(pair[1]) == "CC(=O)[O-]"
    assert np.isclose(pka, 4.81062174)
    assert idx == 3


def test_fumaric_acid():
    # https://www.waters.com/nextgen/ca/en/library/application-notes/2020/analysis-of-organic-acids-using-a-mixed-mode-lc-column-and-an-acquity-qda-mass-detector.html
    mol = Chem.MolFromSmiles("O=C(O)/C=C/C(=O)O")
    molpairs = calculate_microstate_pka_values(mol)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")

    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O=C(O)/C=C/C(=O)O"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])/C=C/C(=O)O"
    assert np.isclose(pka, 3.52694106)
    assert idx == 2 or idx == 7
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "O=C([O-])/C=C/C(=O)O"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])/C=C/C(=O)[O-]"
    assert np.isclose(pka, 4.94770622)
    assert idx == 2 or idx == 7

    ################################################
    ################################################
    # molpairs = calculate_microstate_pka_values(mol, only_dimorphite=True)
    # ################################################
    # protonation_state = 0
    # pka, pair, idx = (
    #     molpairs[protonation_state][0],
    #     molpairs[protonation_state][1],
    #     molpairs[protonation_state][2],
    # )
    # print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    # assert Chem.MolToSmiles(pair[0]) == "O=C(O)/C=C/C(=O)O"
    # assert Chem.MolToSmiles(pair[1]) == "O=C([O-])/C=C/C(=O)O"
    # assert np.isclose(pka, 3.52694106)
    # assert idx == 2
    # ################################################
    # protonation_state = 1
    # pka, pair, idx = (
    #     molpairs[protonation_state][0],
    #     molpairs[protonation_state][1],
    #     molpairs[protonation_state][2],
    # )
    # print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    # assert Chem.MolToSmiles(pair[0]) == "O=C([O-])/C=C/C(=O)O"
    # assert Chem.MolToSmiles(pair[1]) == "O=C([O-])/C=C/C(=O)[O-]"
    # assert np.isclose(pka, 4.94770622)
    # assert idx == 7


def test_malic_acid():
    # https://www.waters.com/nextgen/ca/en/library/application-notes/2020/analysis-of-organic-acids-using-a-mixed-mode-lc-column-and-an-acquity-qda-mass-detector.html
    mol = Chem.MolFromSmiles("O=C(O)CC(O)C(=O)O")

    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")

    assert len(molpairs) == 3
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "O=C(O)CC(O)C(=O)O"
    assert Chem.MolToSmiles(pair[1]) == "O=C(O)CC(O)C(=O)[O-]"
    assert np.isclose(pka, 2.79113841)
    assert idx == 8
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "O=C(O)CC(O)C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])CC(O)C(=O)[O-]"
    assert np.isclose(pka, 3.86118364)
    assert idx == 2
    ################################################
    protonation_state = 2
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O=C([O-])CC(O)C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])CC([O-])C(=O)[O-]"
    assert np.isclose(pka, 12.24020576)
    assert idx == 5


def test_citric_acid():
    # https://www.waters.com/nextgen/ca/en/library/application-notes/2020/analysis-of-organic-acids-using-a-mixed-mode-lc-column-and-an-acquity-qda-mass-detector.html
    mol = Chem.MolFromSmiles("O=C(O)CC(O)(CC(=O)O)C(=O)O")

    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol)
    assert len(molpairs) == 4
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")

    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "O=C(O)CC(O)(CC(=O)O)C(=O)O"
    assert Chem.MolToSmiles(pair[1]) == "O=C(O)CC(O)(CC(=O)O)C(=O)[O-]"
    assert np.isclose(pka, 2.97935152)
    assert idx == 12

    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "O=C(O)CC(O)(CC(=O)O)C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])CC(O)(CC(=O)O)C(=O)[O-]"
    assert np.isclose(pka, 3.93864965)
    assert idx == 2 or idx == 9

    ################################################
    protonation_state = 2
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "O=C([O-])CC(O)(CC(=O)O)C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])CC(O)(CC(=O)[O-])C(=O)[O-]"
    assert np.isclose(pka, 4.28753757)
    assert idx == 9 or idx == 2
    ################################################
    protonation_state = 3
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O=C([O-])CC(O)(CC(=O)[O-])C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])CC([O-])(CC(=O)[O-])C(=O)[O-]"
    assert np.isclose(pka, 12.02427483)
    assert idx == 5


def test_ascorbic_acid():
    # https://www.waters.com/nextgen/ca/en/library/application-notes/2020/analysis-of-organic-acids-using-a-mixed-mode-lc-column-and-an-acquity-qda-mass-detector.html
    mol = Chem.MolFromSmiles("C(C(C1C(=C(C(=O)O1)O)O)O)O")

    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "O=C1OC(C(O)CO)C(O)=C1O"
    assert Chem.MolToSmiles(pair[1]) == "O=C1OC(C(O)CO)C([O-])=C1O"
    assert np.isclose(pka, 3.39439988)
    assert idx == 9

    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O=C1OC(C(O)CO)C([O-])=C1O"
    assert Chem.MolToSmiles(pair[1]) == "O=C1OC(C(O)C[O-])C([O-])=C1O"
    assert np.isclose(pka, 9.08883286)
    assert idx == 7
    ################################################
    protonation_state = 2
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O=C1OC(C(O)C[O-])C([O-])=C1O"
    assert Chem.MolToSmiles(pair[1]) == "O=C1OC(C([O-])C[O-])C([O-])=C1O"
    assert np.isclose(pka, 10.539691925048828)
    assert idx == 5


def test_quinic_acid():
    # https://www.waters.com/nextgen/ca/en/library/application-notes/2020/analysis-of-organic-acids-using-a-mixed-mode-lc-column-and-an-acquity-qda-mass-detector.html
    mol = Chem.MolFromSmiles("O=C(O)[C@]1(O)C[C@@H](O)[C@@H](O)[C@H](O)C1")

    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")

    ################################################
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert Chem.MolToSmiles(pair[0]) == "O=C(O)[C@]1(O)C[C@@H](O)[C@@H](O)[C@H](O)C1"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])[C@]1(O)C[C@@H](O)[C@@H](O)[C@H](O)C1"
    assert np.isclose(pka, 3.7188952)
    assert idx == 2
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O=C([O-])[C@]1(O)C[C@@H](O)[C@@H](O)[C@H](O)C1"
    assert (
        Chem.MolToSmiles(pair[1]) == "O=C([O-])[C@]1([O-])C[C@@H](O)[C@@H](O)[C@H](O)C1"
    )
    assert np.isclose(pka, 12.78168488)
    assert idx == 4
    ################################################


def test_cocaine():
    # https://www.waters.com/nextgen/ca/en/library/application-notes/2020/analysis-of-organic-acids-using-a-mixed-mode-lc-column-and-an-acquity-qda-mass-detector.html
    mol = Chem.MolFromSmiles("COC(=O)C1C(OC(=O)C2=CC=CC=C2)CC2CCC1N2C")

    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")

    assert len(molpairs) == 1
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "COC(=O)C1C(OC(=O)c2ccccc2)CC2CCC1[NH+]2C"
    assert Chem.MolToSmiles(pair[1]) == "COC(=O)C1C(OC(=O)c2ccccc2)CC2CCC1N2C"
    assert np.isclose(pka, 8.055152893066406)
    assert idx == 20
    ################################################


def test_tyrosine():
    # https://chem.libretexts.org/Courses/University_of_Arkansas_Little_Rock/CHEM_4320_5320%3A_Biochemistry_1/01%3A_Amino_Acids/1.4%3A_Reactions_of_Amino_Acids/1.4.1_Acid-base_Chemistry_of_Amino_Acids
    mol = Chem.MolFromSmiles("NC(CC1=CC=C(O)C=C1)C(=O)O")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 3
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+]C(Cc1ccc(O)cc1)C(=O)O"
    assert Chem.MolToSmiles(pair[1]) == "[NH3+]C(Cc1ccc(O)cc1)C(=O)[O-]"
    assert np.isclose(pka, 2.2737984657287598)
    assert idx == 12
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+]C(Cc1ccc(O)cc1)C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "[NH3+]C(Cc1ccc([O-])cc1)C(=O)[O-]"
    assert np.isclose(pka, 8.993396759033203)
    assert idx == 7
    ################################################
    protonation_state = 2
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+]C(Cc1ccc([O-])cc1)C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "NC(Cc1ccc([O-])cc1)C(=O)[O-]"
    assert np.isclose(pka, 9.486579895019531)
    assert idx == 0
    ################################################


def test_aspartic_acid():
    # https://chem.libretexts.org/Courses/University_of_Arkansas_Little_Rock/CHEM_4320_5320%3A_Biochemistry_1/01%3A_Amino_Acids/1.4%3A_Reactions_of_Amino_Acids/1.4.1_Acid-base_Chemistry_of_Amino_Acids
    mol = Chem.MolFromSmiles("N[C@@H](CC(=O)O)C(=O)O")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 3
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+][C@@H](CC(=O)O)C(=O)O"
    assert Chem.MolToSmiles(pair[1]) == "[NH3+][C@@H](CC(=O)O)C(=O)[O-]"
    assert np.isclose(pka, 2.21097993850708)
    assert idx == 8
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+][C@@H](CC(=O)O)C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "[NH3+][C@@H](CC(=O)[O-])C(=O)[O-]"
    assert np.isclose(pka, 3.519895076751709)
    assert idx == 5
    ################################################
    protonation_state = 2
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+][C@@H](CC(=O)[O-])C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "N[C@@H](CC(=O)[O-])C(=O)[O-]"
    assert np.isclose(pka, 9.840612411499023)
    assert idx == 0
    ################################################


def test_taurin():
    # http://www2.chm.ulaval.ca/gecha/chm1903/4_acide-base/organic_acids.pdf
    mol = Chem.MolFromSmiles("NCCS(=O)(=O)O")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 1
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+]CCS(=O)(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "NCCS(=O)(=O)[O-]"
    assert np.isclose(pka, 9.672035217285156)
    assert idx == 0
    ################################################


def test_cysteamine():
    # http://www2.chm.ulaval.ca/gecha/chm1903/4_acide-base/organic_acids.pdf
    mol = Chem.MolFromSmiles("NCCS")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 3
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+]CC[SH2+]"
    assert Chem.MolToSmiles(pair[1]) == "[NH3+]CCS"
    assert np.isclose(pka, 1.9965983629226685)
    assert idx == 3
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+]CCS"
    assert Chem.MolToSmiles(pair[1]) == "[NH3+]CC[S-]"
    assert np.isclose(pka, 8.375046730041504)
    assert idx == 3
    ################################################
    protonation_state = 2
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+]CC[S-]"
    assert Chem.MolToSmiles(pair[1]) == "NCC[S-]"
    assert np.isclose(pka, 10.587972640991211)
    assert idx == 0
    ################################################


def test_diphonoethane():
    # http://www2.chm.ulaval.ca/gecha/chm1903/4_acide-base/organic_acids.pdf
    mol = Chem.MolFromSmiles("CC(O)(P(=O)(O)O)P(=O)(O)O")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 4
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "CC(O)(P(=O)(O)O)P(=O)(O)O"
    assert Chem.MolToSmiles(pair[1]) == "CC(O)(P(=O)([O-])O)P(=O)(O)O"
    assert np.isclose(pka, 2.3572850227355957)
    assert idx == 9 or idx == 5  # symmetric mol
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "CC(O)(P(=O)([O-])O)P(=O)(O)O"
    assert Chem.MolToSmiles(pair[1]) == "CC(O)(P(=O)([O-])O)P(=O)([O-])O"
    assert np.isclose(pka, 2.4741861820220947)
    assert idx == 5 or idx == 9  # symmetric mol
    ################################################
    protonation_state = 2
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "CC(O)(P(=O)([O-])O)P(=O)([O-])O"
    assert Chem.MolToSmiles(pair[1]) == "CC(O)(P(=O)([O-])[O-])P(=O)([O-])O"
    assert np.isclose(pka, 5.930602550506592)
    assert idx == 6
    ################################################
    protonation_state = 3
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "CC(O)(P(=O)([O-])[O-])P(=O)([O-])O"
    assert Chem.MolToSmiles(pair[1]) == "CC(O)(P(=O)([O-])[O-])P(=O)([O-])[O-]"
    assert np.isclose(pka, 10.735816955566406)
    assert idx == 10
    ################################################


def test_arginin():
    # https://chem.libretexts.org/Courses/University_of_Arkansas_Little_Rock/CHEM_4320_5320%3A_Biochemistry_1/01%3A_Amino_Acids/1.4%3A_Reactions_of_Amino_Acids/1.4.1_Acid-base_Chemistry_of_Amino_Acids
    mol = Chem.MolFromSmiles("NC(N)=NCCCC(N)C(=O)O")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 3
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "NC(N)=[NH+]CCCC([NH3+])C(=O)O"
    assert Chem.MolToSmiles(pair[1]) == "NC(N)=[NH+]CCCC([NH3+])C(=O)[O-]"
    assert np.isclose(pka, 2.0857582092285156)
    assert idx == 11
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "NC(N)=[NH+]CCCC([NH3+])C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "NC(N)=[NH+]CCCC(N)C(=O)[O-]"
    assert np.isclose(pka, 9.936403274536133)
    assert idx == 8
    ################################################
    protonation_state = 2
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "NC(N)=[NH+]CCCC(N)C(=O)[O-]"
    assert Chem.MolToSmiles(pair[1]) == "NC(N)=NCCCC(N)C(=O)[O-]"
    assert np.isclose(pka, 11.475444793701172)
    assert idx == 3
    ################################################


def test_thiophenecarboxylicacid():
    # http://www2.chm.ulaval.ca/gecha/chm1903/4_acide-base/organic_acids.pdf
    mol = Chem.MolFromSmiles("O=C(O)C1=CSC=C1")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 1
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O=C(O)c1ccsc1"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])c1ccsc1"
    assert np.isclose(pka, 3.9233970642089844)
    assert idx == 2  # symmetric mol


def test_nitroaniline():
    # http://www2.chm.ulaval.ca/gecha/chm1903/4_acide-base/organic_acids.pdf
    mol = Chem.MolFromSmiles("NC1=CC([N+](=O)[O-])=CC=C1")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 2
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "[NH3+]c1cccc([N+](=O)[O-])c1"
    assert Chem.MolToSmiles(pair[1]) == "Nc1cccc([N+](=O)[O-])c1"
    assert np.isclose(pka, 2.331765651702881)
    assert idx == 0
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "Nc1cccc([N+](=O)[O-])c1"
    assert Chem.MolToSmiles(pair[1]) == "[NH-]c1cccc([N+](=O)[O-])c1"
    assert np.isclose(pka, 11.329208374023438)
    assert idx == 0


def test_benzenesulfinicacid():
    # http://www2.chm.ulaval.ca/gecha/chm1903/4_acide-base/organic_acids.pdf
    mol = Chem.MolFromSmiles("O=S(O)C1=CC=CC=C1")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 1
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O=S(O)c1ccccc1"
    assert Chem.MolToSmiles(pair[1]) == "O=S([O-])c1ccccc1"
    assert np.isclose(pka, 2.209087371826172)
    assert idx == 2


def test_bromobenzoicacid():
    # http://www2.chm.ulaval.ca/gecha/chm1903/4_acide-base/organic_acids.pdf
    mol = Chem.MolFromSmiles("O=C(O)C1=CC(Br)=CC=C1")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 1
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O=C(O)c1cccc(Br)c1"
    assert Chem.MolToSmiles(pair[1]) == "O=C([O-])c1cccc(Br)c1"
    assert np.isclose(pka, 3.643803596496582)
    assert idx == 2


def test_benzaldehyde():
    # http://www2.chm.ulaval.ca/gecha/chm1903/4_acide-base/organic_acids.pdf
    mol = Chem.MolFromSmiles("O=CC1=CC=CC=C1")
    ################################################
    ################################################
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    assert len(molpairs) == 0
    ################################################


def test_mol_00():
    # 00 Chembl molecule
    mol = mollist[0]

    molpairs = calculate_microstate_pka_values(mol)
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
    assert (
        Chem.MolToSmiles(pair[0])
        == "[NH3+]c1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc([NH3+])c5ccccc54)c3)c2)c2ccccc12"
    )
    assert (
        Chem.MolToSmiles(pair[1])
        == "Nc1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc([NH3+])c5ccccc54)c3)c2)c2ccccc12"
    )
    assert np.isclose(pka, 1.861354112625122)
    assert idx == 21 or idx == 0
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert (
        Chem.MolToSmiles(pair[0])
        == "Nc1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc([NH3+])c5ccccc54)c3)c2)c2ccccc12"
    )
    assert (
        Chem.MolToSmiles(pair[1])
        == "Nc1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc(N)c5ccccc54)c3)c2)c2ccccc12"
    )
    assert np.isclose(pka, 2.4510035514831543)
    assert idx == 0 or idx == 21

    ################################################
    protonation_state = 2
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    assert (
        Chem.MolToSmiles(pair[0])
        == "Nc1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc(N)c5ccccc54)c3)c2)c2ccccc12"
    )
    assert (
        Chem.MolToSmiles(pair[1])
        == "[NH-]c1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc(N)c5ccccc54)c3)c2)c2ccccc12"
    )

    assert np.isclose(pka, 11.28736496)
    assert idx == 0 or idx == 21
    ################################################
    protonation_state = 3
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert (
        Chem.MolToSmiles(pair[0])
        == "[NH-]c1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc(N)c5ccccc54)c3)c2)c2ccccc12"
    )
    assert (
        Chem.MolToSmiles(pair[1])
        == "[NH-]c1cc[n+](Cc2cccc(-c3cccc(C[n+]4ccc([NH-])c5ccccc54)c3)c2)c2ccccc12"
    )

    assert np.isclose(pka, 11.68689919)
    assert idx == 21 or idx == 0

    print("#####################################################")
    print("#####################################################")


def test_mol_14():
    # 14th Chembl molecule
    mol = mollist[14]
    molpairs = calculate_microstate_pka_values(mol, only_dimorphite=False)
    print(len(molpairs))
    # assert len(molpairs) ==
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )

    assert Chem.MolToSmiles(pair[0]) == "O[NH2+]C1c2cc(O)c(O)cc2-c2cc(O)c(O)cc21"
    assert Chem.MolToSmiles(pair[1]) == "ONC1c2cc(O)c(O)cc2-c2cc(O)c(O)cc21"
    assert np.isclose(pka, 5.003658771514893)
    assert idx == 1


def test_mol_20():
    # 20th Chembl molecule
    mol = mollist[20]
    molpairs = calculate_microstate_pka_values(mol)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    assert (
        Chem.MolToSmiles(pair[0])
        == "CC1(C)C2=CCC3C4CC[C@H](OC5CC5)[C@@]4(C)CCC3[C@@]2(C)CC[C@@H]1O"
    )
    assert (
        Chem.MolToSmiles(pair[1])
        == "CC1(C)C2=CCC3C4CC[C@H](OC5CC5)[C@@]4(C)CCC3[C@@]2(C)CC[C@@H]1[O-]"
    )

    assert np.isclose(pka, 11.335731506347656)
    assert idx == 25


def test_mol_58():
    # 58th Chembl molecule
    mol = mollist[58]
    molpairs = calculate_microstate_pka_values(mol)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    assert Chem.MolToSmiles(pair[0]) == "CCCCCC[NH+]1CC[NH+]2CC(c3ccccc3)c3ccccc3C2C1"
    assert Chem.MolToSmiles(pair[1]) == "CCCCCCN1CC[NH+]2CC(c3ccccc3)c3ccccc3C2C1"

    assert np.isclose(pka, 5.578260898590088)
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    assert Chem.MolToSmiles(pair[0]) == "CCCCCCN1CC[NH+]2CC(c3ccccc3)c3ccccc3C2C1"
    assert Chem.MolToSmiles(pair[1]) == "CCCCCCN1CCN2CC(c3ccccc3)c3ccccc3C2C1"

    assert np.isclose(pka, 8.16279411315918)


def test_mol_59():
    # 59th Chembl molecule
    mol = mollist[59]
    molpairs = calculate_microstate_pka_values(mol)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    assert (
        Chem.MolToSmiles(pair[0])
        == "CC/C(=C(\c1ccc(I)cc1)c1ccc(OCC[NH+](C)C)cc1)c1ccccc1"
    )
    assert (
        Chem.MolToSmiles(pair[1]) == "CC/C(=C(\c1ccc(I)cc1)c1ccc(OCCN(C)C)cc1)c1ccccc1"
    )
    assert np.isclose(pka, 8.48440170288086)


def test_mol_62():
    # 62th Chembl molecule
    mol = mollist[62]
    molpairs = calculate_microstate_pka_values(mol)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    assert (
        Chem.MolToSmiles(pair[0]) == "Cc1cc(CCCCCOc2ccc(-c3[nH+]c(C)c(C)o3)cc2)o[nH+]1"
    )
    assert Chem.MolToSmiles(pair[1]) == "Cc1cc(CCCCCOc2ccc(-c3nc(C)c(C)o3)cc2)o[nH+]1"
    assert np.isclose(pka, 1.4769623279571533)
    assert idx == 15
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    assert Chem.MolToSmiles(pair[0]) == "Cc1cc(CCCCCOc2ccc(-c3nc(C)c(C)o3)cc2)o[nH+]1"
    assert Chem.MolToSmiles(pair[1]) == "Cc1cc(CCCCCOc2ccc(-c3nc(C)c(C)o3)cc2)on1"
    assert np.isclose(pka, 2.3255257606506348)
    assert idx == 24


def test_mol_70():
    # 70th Chembl molecule
    mol = mollist[70]
    molpairs = calculate_microstate_pka_values(mol)
    ################################################
    print("################################")
    for i in range(len(molpairs)):
        pka, pair, idx = (
            molpairs[i][0],
            molpairs[i][1],
            molpairs[i][2],
        )
        print(Chem.MolToSmiles(pair[0]), Chem.MolToSmiles(pair[1]))
        print(pka)
    print("################################")
    ################################################
    ################################################
    protonation_state = 0
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    assert (
        Chem.MolToSmiles(pair[0]) == "Oc1ccc(/C(=C(/c2ccc(O)cc2)C(F)(F)F)C(F)(F)F)cc1"
    )
    assert (
        Chem.MolToSmiles(pair[1])
        == "[O-]c1ccc(/C(=C(/c2ccc(O)cc2)C(F)(F)F)C(F)(F)F)cc1"
    )
    assert np.isclose(pka, 7.991166591644287)
    assert idx == 0 or idx == 11
    ################################################
    protonation_state = 1
    pka, pair, idx = (
        molpairs[protonation_state][0],
        molpairs[protonation_state][1],
        molpairs[protonation_state][2],
    )
    assert (
        Chem.MolToSmiles(pair[0])
        == "[O-]c1ccc(/C(=C(/c2ccc(O)cc2)C(F)(F)F)C(F)(F)F)cc1"
    )
    assert (
        Chem.MolToSmiles(pair[1])
        == "[O-]c1ccc(/C(=C(/c2ccc([O-])cc2)C(F)(F)F)C(F)(F)F)cc1"
    )
    assert np.isclose(pka, 9.038616180419922)
    assert idx == 11 or idx == 0
