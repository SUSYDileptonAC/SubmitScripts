import FWCore.ParameterSet.Config as cms
	
process = cms.Process('Analysis')

process.options = cms.untracked.PSet(

     wantSummary = cms.untracked.bool(True)
)
process.MessageLogger = cms.Service('MessageLogger',
  unittest_baseCuts_SUSY_LM0_Cern = cms.untracked.PSet( 
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
  destinations = cms.untracked.vstring('unittest_baseCuts_SUSY_LM0_Cern')
)

process.source = cms.Source('PoolSource', 
     duplicateCheckMode = cms.untracked.string('noDuplicateCheck'),
     fileNames = cms.untracked.vstring()
)

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1))


process.TFileService = cms.Service('TFileService', fileName = cms.string('unittest.baseCuts.SUSY_LM0_Cern.root'))



	
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


rej_Cuts = cms.untracked.bool(False), 
rej_JetCut = cms.untracked.bool(True),
rej_METCut = cms.untracked.bool(True), 

rej_LeptonCut = cms.untracked.string("2Leptons"),
rej_bTagCut = cms.untracked.bool(False),

# not working properly, yet
user_nPos_Electrons = cms.untracked.int32(0),
user_nNeg_Electrons = cms.untracked.int32(0),
user_nPos_Muons = cms.untracked.int32(1),
user_nNeg_Muons = cms.untracked.int32(1),

user_nJets = cms.untracked.int32(4), #if 0 sum of 4Jets is checked
user_nbJets = cms.untracked.int32(2), #exactly the number of b_jets
user_pt1JetMin = cms.untracked.double(120.),
user_pt2JetMin = cms.untracked.double(80.),
user_pt3JetMin = cms.untracked.double(80.),
user_pt4JetMin = cms.untracked.double(80.),
user_METMin = cms.untracked.double(50.),
user_bTagDiscriminator = cms.untracked.double(0.4),

# muons
acc_MuonPt = cms.untracked.double(10.),
acc_MuonEta = cms.untracked.double(2.1),
acc_MuonChi2 = cms.untracked.double(10.),
acc_Muond0 = cms.untracked.double(0.2),
acc_MuonnHits = cms.untracked.double(11),
iso_MuonIso = cms.untracked.double(0.2),
iso_MuonHCALIso = cms.untracked.double(6.0),
iso_MuonECALIso = cms.untracked.double(4.0),

# electrons
user_ElectronID = cms.untracked.string("eidTight"),
acc_ElectronPt = cms.untracked.double(10.),
acc_ElectronEta = cms.untracked.double(2.5),
acc_Electrond0 = cms.untracked.double(0.2),
iso_ElectronIso = cms.untracked.double(0.4),

# jets
acc_JetPt = cms.untracked.double(30.),
acc_JetEta = cms.untracked.double(2.4),
acc_JetEMF = cms.untracked.double(0.1),


# tag and probe method
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
