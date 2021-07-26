from rdkit import Chem
from rdkit.Chem.AllChem import GetMorganFingerprintAsBitVect
import numpy as np

def create_conjugate(mol, id, pka, pH=7.4):
    """Create a new molecule that is the conjugated base/acid to the input molecule."""
    mol = Chem.RWMol(mol)
    atom = mol.GetAtomWithIdx(id)
    charge = atom.GetFormalCharge()
    Ex_Hs = atom.GetNumExplicitHs()
    Tot_Hs = atom.GetTotalNumHs()

#with correction for +2 charges            
    if  (pka > pH and Tot_Hs > 0) or charge > 0:
        atom.SetFormalCharge(charge - 1)
        if Ex_Hs > 0:
            atom.SetNumExplicitHs(Ex_Hs - 1)
            
    elif pka < pH and charge <= 0:
        atom.SetFormalCharge(charge + 1)
        if Tot_Hs == 0 or Ex_Hs > 0:
            atom.SetNumExplicitHs(Ex_Hs + 1)
    
    else:
        # pka > pH and Tot_Hs = 0
        atom.SetFormalCharge(charge + 1)
        if Tot_Hs == 0 or Ex_Hs > 0:
            atom.SetNumExplicitHs(Ex_Hs + 1)

    atom.UpdatePropertyCache()
    return mol

def morgan_fp_array(df, mol_column, nBits=4096, radius=3, useFeatures=True):
    """Take Pandas DataFrame, create Morgan fingerprints from the molecules in "mol_column"
    and return them as numpy array.
    """
    length = len(df)
    i = 0
    for mol in df[mol_column]:
        
        fp = np.array(GetMorganFingerprintAsBitVect(
            mol, radius=3, nBits=4096, useFeatures=useFeatures
        ))
        if i == 0:
            array = fp
        else:
            array = np.vstack((array, fp))
        if i%1000 == 0:
            print(f'fp:{i} of {length}')
        i += 1
    return array

#return whether a bond matches a particular smarts query
def bond_smarts_query(bond, smarts):
    for match in bond.GetOwningMol().GetSubstructMatches(Chem.MolFromSmarts(smarts)):
        if set((bond.GetBeginAtomIdx(),bond.GetEndAtomIdx())) == set(match):
            return True
    return False

def atom_smarts_query(atom, smarts):
    if atom.GetOwningMol().GetSubstructMatches(Chem.MolFromSmarts(smarts)):
        if atom.GetIdx() in atom.GetOwningMol().GetSubstructMatches(Chem.MolFromSmarts(smarts))[0]:
                return True
    return False

def tanimoto(fp1, fp2):
    set1= set(fp1.nonzero()[0].tolist())
    set2= set(fp2.nonzero()[0].tolist())
    return len(set1&set2)/len(set1|set2)