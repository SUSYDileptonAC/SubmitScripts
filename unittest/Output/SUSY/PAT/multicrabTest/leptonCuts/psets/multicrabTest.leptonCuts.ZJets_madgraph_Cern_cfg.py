import FWCore.ParameterSet.Config as cms
	
process = cms.Process('Analysis')

process.options = cms.untracked.PSet(

     wantSummary = cms.untracked.bool(True)
)
process.MessageLogger = cms.Service('MessageLogger',
  multicrabTest_leptonCuts_ZJets_madgraph_Cern = cms.untracked.PSet( 
     INFO = cms.untracked.PSet(
          limit = cms.untracked.int32(0)
     ),
     FwkReport = cms.untracked.PSet(
          reportEvery = cms.untracked.int32(1000),
          limit = cms.untracked.int32(1000)
     ),
     default = cms.untracked.PSet(
          limit = cms.untracked.int32(100)
     ),
     Root_NoDictionary = cms.untracked.PSet(
          limit = cms.untracked.int32(0)
     ),
     FwkJob = cms.untracked.PSet(
          limit = cms.untracked.int32(0)
     ),
     FwkSummary = cms.untracked.PSet(
          reportEvery = cms.untracked.int32(1),
          limit = cms.untracked.int32(10000000)
     ),
     threshold = cms.untracked.string('INFO')
  ),
  destinations = cms.untracked.vstring('multicrabTest_leptonCuts_ZJets_madgraph_Cern')
)

process.source = cms.Source('PoolSource', 
     duplicateCheckMode = cms.untracked.string('noDuplicateCheck'),
     fileNames = cms.untracked.vstring()
)

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1))


process.TFileService = cms.Service('TFileService', fileName = cms.string('multicrabTest.leptonCuts.ZJets_madgraph_Cern.root'))



	
process.DiLeptonAnalysis = cms.EDAnalyzer('SUSYDiLeptonAnalysis',
										  
debug = cms.untracked.bool(False),
mcInfo = cms.untracked.bool(False),

mcSource = cms.InputTag("genParticles"),
beamSpotSource = cms.InputTag("offlineBeamSpot"),
trackSource = cms.InputTag("generalTracks"),
muonSource = cms.InputTag("allLayer1Muons"),
electronSource = cms.InputTag("allLayer1Electrons"),
metSource = cms.InputTag("allLayer1METsSC5"),
jetSource = cms.InputTag("allLayer1JetsSC5"),

user_bJetAlgo = cms.untracked.string("jetProbabilityBJetTags"),

CSA_weighted = cms.untracked.bool(False),

rej_Cuts = cms.untracked.bool(True), 
rej_JetCut = cms.untracked.bool(False),
rej_METCut = cms.untracked.bool(False), 
rej_LeptonCut = cms.untracked.string("OS"),
rej_bTagCut = cms.untracked.bool(False),

user_nPos_Electrons = cms.untracked.int32(1), 
user_nNeg_Electrons = cms.untracked.int32(1), 
user_nPos_Muons = cms.untracked.int32(0), 
user_nNeg_Muons = cms.untracked.int32(0), 

user_nJets = cms.untracked.int32(3), #if 0 sum of 4Jets is checked
user_nbJets = cms.untracked.int32(2), #exactly the number of b_jets

user_pt1JetMin = cms.untracked.double(100.),
user_pt2JetMin = cms.untracked.double(50.),
user_pt3JetMin = cms.untracked.double(50.),
user_pt4JetMin = cms.untracked.double(0.),

user_METMin = cms.untracked.double(100.),

user_bTagDiscriminator = cms.untracked.double(0.4),

acc_MuonPt = cms.untracked.double(10.), 
acc_MuonEta = cms.untracked.double(2.), 
acc_MuonChi2 = cms.untracked.double(10.),
acc_MuonnHits = cms.untracked.double(11.),
acc_Muond0 = cms.untracked.double(0.2),
iso_MuonIso = cms.untracked.double(0.2),
    
user_ElectronID = cms.untracked.string("eidTight"),
acc_ElectronPt = cms.untracked.double(10.), 
acc_ElectronEta = cms.untracked.double(2.), 
acc_Electrond0 = cms.untracked.double(0.2),
iso_ElectronIso = cms.untracked.double(0.4), 
    
acc_JetPt = cms.untracked.double(30.), 
acc_JetEta = cms.untracked.double(2.5),

tnp_method =  cms.untracked.string("False"),
tnp_tag_dr = cms.untracked.double(0.1),
tnp_tag_pt = cms.untracked.double(10.),
tnp_tag_eta = cms.untracked.double(2.),
tnp_low_SB1 = cms.untracked.double(40.),
tnp_high_SB1 = cms.untracked.double(60.),
tnp_low_inv = cms.untracked.double(80.),
tnp_high_inv = cms.untracked.double(100.),
tnp_low_SB2 = cms.untracked.double(120.),
tnp_high_SB2 = cms.untracked.double(140.)


)

process.p = cms.Path(process.DiLeptonAnalysis)
