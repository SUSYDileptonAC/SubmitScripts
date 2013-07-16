import FWCore.ParameterSet.Config as cms

process = cms.Process('Analysis')

process.options = cms.untracked.PSet(

     wantSummary = cms.untracked.bool(True)
)
process.MessageLogger = cms.Service('MessageLogger',
  unittest_baseCutsotherCuts_SUSY_LM0_Cern = cms.untracked.PSet( 
     INFO = cms.untracked.PSet(
          limit = cms.untracked.int32(0)
     ),
     FwkReport = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          reportEvery = cms.untracked.int32(1000),
          limit = cms.untracked.int32(1000)
     ),
     default = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          limit = cms.untracked.int32(100)
     ),
     Root_NoDictionary = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          limit = cms.untracked.int32(0)
     ),
     FwkJob = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          limit = cms.untracked.int32(0)
     ),
     FwkSummary = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          reportEvery = cms.untracked.int32(1),
          limit = cms.untracked.int32(10000000)
     ),
     threshold = cms.untracked.string('INFO')
  ),
  destinations = cms.untracked.vstring('unittest_baseCutsotherCuts_SUSY_LM0_Cern')
)

process.source = cms.Source('PoolSource', 
     duplicateCheckMode = cms.untracked.string('noDuplicateCheck'),
     fileNames = cms.untracked.vstring()
)

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1))



##--- GlobalTag


########## Additional Producers ########################
from SuSyAachen.Skimming.defaults.SUSYPAT_cff import SUSYPAT
SUSYPAT(process)


########## Filters ########################


#--- Task: baseCuts
import SuSyAachen.Skimming.defaults.taus_cfi

process.baseCutstaus0 = SuSyAachen.Skimming.defaults.taus_cfi.defaultSelector.clone(
	src = 'cleanLayer1Taus',
	cut = 'abs( eta ) <= 2.5 & pt >= 7',
)

process.baseCutstaus1 = SuSyAachen.Skimming.defaults.taus_cfi.defaultSelector.clone(
	src = 'baseCutstaus0',
	cut = 'leadPFChargedHadrCand.trackRef.numberOfValidHits >= 11&(signalPFChargedHadrCands.size = 1 | signalPFChargedHadrCands.size = 3)& abs(charge) = 1',
)

process.baseCutsIsoTaus = SuSyAachen.Skimming.defaults.taus_cfi.defaultSelector.clone(
	src = 'baseCutstaus1',
	cut = 'isolationPFChargedHadrCandsPtSum <= 1 & isolationPFChargedHadrCandsPtSum/pt <= 0.05',
)
import SuSyAachen.Skimming.defaults.met_cfi

process.baseCutsMETFilter = SuSyAachen.Skimming.defaults.met_cfi.defaultSelector.clone(
	src = 'layer1METsAK5',
	cut = 'pt >= 100',
)
import SuSyAachen.Skimming.defaults.electrons_cfi

process.baseCutselectrons0 = SuSyAachen.Skimming.defaults.electrons_cfi.defaultSelector.clone(
	src = 'cleanLayer1Electrons',
	cut = 'abs( eta ) <= 2.0 & pt >= 10',
)

process.baseCutselectrons1 = SuSyAachen.Skimming.defaults.electrons_cfi.defaultSelector.clone(
	src = 'baseCutselectrons0',
	cut = 'electronID("eidTight")==1.0',
)

process.baseCutselectrons2 = SuSyAachen.Skimming.defaults.electrons_cfi.PATElectronD0Selector.clone(
	beamSpotSource = 'offlineBeamSpot',
	src = 'baseCutselectrons1',
	d0Min = 0.20000000000000001,
)

process.baseCutsIsoElectrons = SuSyAachen.Skimming.defaults.electrons_cfi.defaultSelector.clone(
	src = 'baseCutselectrons2',
	cut = '(trackIso + ecalIso + hcalIso) / pt <= 0.4',
)
import SuSyAachen.Skimming.defaults.jets_cfi

process.baseCutsBaseJets = SuSyAachen.Skimming.defaults.jets_cfi.defaultSelector.clone(
	src = 'cleanLayer1JetsAK5',
	cut = 'abs( eta ) <= 2.5 & pt >= 50',
)

process.baseCutsJetFilterHigh = SuSyAachen.Skimming.defaults.jets_cfi.patJetCountFilter.clone(
	src = 'baseCutsBaseJets',
	cut = 'abs( eta ) <= 2.5 & pt >= 100',
	minNumber = 1,
)

process.baseCutsJetFilterLow = SuSyAachen.Skimming.defaults.jets_cfi.patJetCountFilter.clone(
	src = 'baseCutsBaseJets',
	cut = 'abs( eta ) <= 2.5 & pt >= 50',
	minNumber = 3,
)
import SuSyAachen.Skimming.defaults.muons_cfi

process.baseCutsbasicMuons = SuSyAachen.Skimming.defaults.muons_cfi.defaultSelector.clone(
	src = 'cleanLayer1Muons',
	cut = 'abs( eta ) <= 2.0 & pt >= 10',
)

process.baseCutsglobalMuons = SuSyAachen.Skimming.defaults.muons_cfi.defaultSelector.clone(
	src = 'baseCutsbasicMuons',
	cut = "muonID( 'AllGlobalMuons' )",
)

process.baseCutsqualityMuons = SuSyAachen.Skimming.defaults.muons_cfi.defaultSelector.clone(
	src = 'baseCutsglobalMuons',
	cut = 'globalTrack.normalizedChi2 <= 10. & track.numberOfValidHits >= 11.',
)

process.baseCutsd0Muons = SuSyAachen.Skimming.defaults.muons_cfi.PATMuonD0Selector.clone(
	beamSpotSource = 'offlineBeamSpot',
	src = 'baseCutsqualityMuons',
	d0Min = 0.20000000000000001,
)

process.baseCutsIsoMuons = SuSyAachen.Skimming.defaults.muons_cfi.defaultSelector.clone(
	src = 'baseCutsd0Muons',
	cut = '(trackIso + ecalIso + hcalIso) / pt <= 0.2',
)
process.seqbaseCuts = cms.Sequence(cms.ignore(process.baseCutsBaseJets) * cms.ignore(process.baseCutsJetFilterHigh) * cms.ignore(process.baseCutsJetFilterLow) * cms.ignore(process.baseCutstaus0) * cms.ignore(process.baseCutstaus1) * cms.ignore(process.baseCutsIsoTaus) * cms.ignore(process.baseCutselectrons0) * cms.ignore(process.baseCutselectrons1) * cms.ignore(process.baseCutselectrons2) * cms.ignore(process.baseCutsIsoElectrons) * cms.ignore(process.baseCutsbasicMuons) * cms.ignore(process.baseCutsglobalMuons) * cms.ignore(process.baseCutsqualityMuons) * cms.ignore(process.baseCutsd0Muons) * cms.ignore(process.baseCutsIsoMuons) * cms.ignore(process.baseCutsMETFilter))
#--- Task: otherCuts
import SuSyAachen.Skimming.defaults.taus_cfi

process.otherCutstaus0 = SuSyAachen.Skimming.defaults.taus_cfi.defaultSelector.clone(
	src = 'cleanLayer1Taus',
	cut = 'abs( eta ) <= 2.0 & pt >= 20',
)
import SuSyAachen.Skimming.defaults.met_cfi

process.otherCutsMETFilter = SuSyAachen.Skimming.defaults.met_cfi.defaultSelector.clone(
	src = 'layer1METsAK5',
	cut = 'pt >= 100',
)
import SuSyAachen.Skimming.defaults.electrons_cfi

process.otherCutselectrons0 = SuSyAachen.Skimming.defaults.electrons_cfi.defaultSelector.clone(
	src = 'cleanLayer1Electrons',
	cut = 'abs( eta ) <= 2.0 & pt >= 20',
)
import SuSyAachen.Skimming.defaults.jets_cfi

process.otherCutsBaseJets = SuSyAachen.Skimming.defaults.jets_cfi.defaultSelector.clone(
	src = 'cleanLayer1JetsAK5',
	cut = 'abs( eta ) <= 2.5 & pt >= 50',
)

process.otherCutsJetFilterHigh = SuSyAachen.Skimming.defaults.jets_cfi.patJetCountFilter.clone(
	src = 'otherCutsBaseJets',
	cut = 'abs( eta ) <= 2.5 & pt >= 100',
	minNumber = 1,
)

process.otherCutsJetFilterLow = SuSyAachen.Skimming.defaults.jets_cfi.patJetCountFilter.clone(
	src = 'otherCutsBaseJets',
	cut = 'abs( eta ) <= 2.5 & pt >= 50',
	minNumber = 3,
)
import SuSyAachen.Skimming.defaults.muons_cfi

process.otherCutsbasicMuons = SuSyAachen.Skimming.defaults.muons_cfi.defaultSelector.clone(
	src = 'cleanLayer1Muons',
	cut = 'abs( eta ) <= 2.0 & pt >= 20',
)
process.seqotherCuts = cms.Sequence(cms.ignore(process.otherCutsBaseJets) * cms.ignore(process.otherCutsJetFilterHigh) * cms.ignore(process.otherCutsJetFilterLow) * cms.ignore(process.otherCutstaus0) * cms.ignore(process.otherCutselectrons0) * cms.ignore(process.otherCutsbasicMuons) * cms.ignore(process.otherCutsMETFilter))


########## DiLeptonAnalyzers ##############
from SuSyAachen.DiLeptonHistograms.DiLeptonHistograms_cfi import DiLeptonAnalysis

process.baseCutsnoTask = DiLeptonAnalysis.clone(	
debug = False,
mcInfo = False,
CSA_weighted = False,
	
mcSource = "genParticles",
electronSource = "cleanLayer1Electrons",
muonSource = "cleanLayer1Muons",
metSource = "layer1METsAK5",
jetSource = "cleanLayer1JetsAK5"
)
process.baseCutsPath =cms.Path(process.baseCutsMETFilter * process.baseCutsJetFilterLow * process.baseCutsJetFilterHigh * process.baseCutsnoTask)

process.otherCutsnoTask = DiLeptonAnalysis.clone(	
debug = False,
mcInfo = False,
CSA_weighted = False,
	
mcSource = "genParticles",
electronSource = "cleanLayer1Electrons",
muonSource = "cleanLayer1Muons",
metSource = "layer1METsAK5",
jetSource = "cleanLayer1JetsAK5"
)
process.otherCutsPath =cms.Path(process.otherCutsMETFilter * process.otherCutsJetFilterLow * process.otherCutsJetFilterHigh * process.otherCutsnoTask)


########## Output ##############
process.TFileService = cms.Service('TFileService', fileName = cms.string('unittest.baseCutsotherCuts.SUSY_LM0_Cern.root'))




process.out = cms.OutputModule("PoolOutputModule",
  fileName = cms.untracked.string('unittest.baseCutsotherCuts.SUSY_LM0_Cern.EDM.root'),
  outputCommands = cms.untracked.vstring(
    'drop *',
    'keep patElectrons_*_*_*',
    'keep patMuons_*_*_*',
    'keep patTaus_*_*_*',
    'keep recoGenParticles_*_*_*',
    'keep recoGenJets_*_*_*',
    'drop *_genParticles_*_*'
  )
)
process.outpath = cms.EndPath(process.out)

########## Paths ##########################
process.producerPath = cms.Path(process.seqSUSYPAT + process.seqbaseCuts + process.seqotherCuts )
process.schedule = cms.Schedule(process.producerPath, process.baseCutsPath, process.otherCutsPath, process.outpath)
