import FWCore.ParameterSet.Config as cms

process = cms.Process("PATIFY")

#-- Message Logger ------------------------------------------------------------
process.load("FWCore.MessageLogger.MessageLogger_cfi")
process.MessageLogger.cerr.threshold  = 'INFO'
process.MessageLogger.categories.append('PATLayer0Summary')
process.MessageLogger.cerr.INFO       = cms.untracked.PSet(
    default          = cms.untracked.PSet( limit = cms.untracked.int32(0)  ),
    PATLayer0Summary = cms.untracked.PSet( limit = cms.untracked.int32(-1) )
)
process.MessageLogger.cerr.FwkReport  = cms.untracked.PSet(
    reportEvery = cms.untracked.int32(100),
    limit = cms.untracked.int32(10000000)
)
process.options   = cms.untracked.PSet( wantSummary = cms.untracked.bool(True) )

#-- Input Source --------------------------------------------------------------
process.source = cms.Source("PoolSource", 
    duplicateCheckMode = cms.untracked.string('noDuplicateCheck'),
    fileNames = cms.untracked.vstring(
      "/store/relval/CMSSW_2_2_3/RelValTTbar/GEN-SIM-RECO/IDEAL_V11_v2/0000/1466166A-32CB-DD11-9779-001A92810AE2.root",
    )
)
process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(150) )
aFile = ""
if len(process.source.fileNames)>0: aFile       = process.source.fileNames[0].lower()
isFastSim   = ("fastsim" in aFile)
doPhotonID  = (not isFastSim and "aodsim" not in aFile)

#-- Geometry ------------------------------------------------------------------
process.load("Configuration.StandardSequences.Geometry_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
if isFastSim: process.GlobalTag.globaltag = cms.string('IDEAL_V12::All')
else:         process.GlobalTag.globaltag = cms.string('IDEAL_V11::All')
process.load("Configuration.StandardSequences.MagneticField_cff")


#-- PAT Layer 0 + 1 -----------------------------------------------------------
process.load("PhysicsTools.PatAlgos.patLayer0_cff")
process.load("PhysicsTools.PatAlgos.patLayer1_cff")

#-- Necessary fixes to run 2.2.X on 2.1.X data --------------------------------
##from PhysicsTools.PatAlgos.tools.cmsswVersionTools import run22XonSummer08AODSIM
##run22XonSummer08AODSIM(process)

#-- ECAL Saturation bug fix ---------------------------------------------------
### Make new ECal RecHit collection ###
if not isFastSim:
  process.load("SUSYBSMAnalysis.CorrectedECalRecHitProducer.correctedecalrechitproducer_cfi")
  process.CorrectedECalRecHitProducer.recHitsEB = cms.InputTag("ecalRecHit","EcalRecHitsEB")
  process.CorrectedECalRecHitProducer.recHitsEE = cms.InputTag("ecalRecHit","EcalRecHitsEE")

### Change ECal input collection for reconstruction ###
process.load("Configuration.StandardSequences.Reconstruction_cff")
process.towerMaker.ecalInputs = cms.VInputTag(cms.InputTag("CorrectedECalRecHitProducer","EcalRecHitsEBcorr",""),
                                              cms.InputTag("CorrectedECalRecHitProducer","EcalRecHitsEEcorr",""))
if isFastSim:
  process.moreRecoJetMET = cms.Sequence( process.muonMETValueMapProducer
                                       * process.muonTCMETValueMapProducer
                                       * process.tcMet
                                       )
else:
  process.load("Configuration.StandardSequences.Reconstruction_cff")
  process.towerMaker.ecalInputs = cms.VInputTag(cms.InputTag("CorrectedECalRecHitProducer","EcalRecHitsEBcorr",""),
                                                cms.InputTag("CorrectedECalRecHitProducer","EcalRecHitsEEcorr",""))
  process.moreRecoJetMET = cms.Sequence( process.CorrectedECalRecHitProducer
                                    * process.caloTowersRec
                                    * process.recoJets
                                    * process.metreco
                                    )
process.patAODJetMETCorrections.remove(process.muonMETValueMapProducer) # otherwise this module is duplicated in process.metreco

#--to fix photon cleaning -----------------------------------------------------
from PhysicsTools.PatAlgos.cleaningLayer0.photonCleaner_cfi import *
process.allLayer0Photons.removeDuplicates    = cms.string('none')
process.allLayer0Photons.removeElectrons     = cms.string('none')

# Remove embedding of superClusters, will keep entire superCluster collection 
process.allLayer1Electrons.embedSuperCluster = cms.bool(False)
process.allLayer1Photons.embedSuperCluster   = cms.bool(False)

#-- redo PhotonID  --------------------------------------------------------------
if doPhotonID:
  process.load("RecoEgamma.PhotonIdentification.photonId_cff")
  if isFastSim: process.PhotonIDProd.barrelEcalRecHitProducer = cms.string('caloRecHits')
  else:         process.PhotonIDProd.barrelEcalRecHitProducer = cms.string('ecalRecHit')
  if isFastSim: process.PhotonIDProd.endcapEcalRecHitProducer = cms.string('caloRecHits')
  else:         process.PhotonIDProd.endcapEcalRecHitProducer = cms.string('ecalRecHit')

#-- JetPlusTrack --------------------------------------------------------------
process.load("JetMETCorrections.Configuration.ZSPJetCorrections219_cff") 
process.load("JetMETCorrections.Configuration.JetPlusTrackCorrections_cff") 
process.JPT = cms.Sequence( process.ZSPJetCorrections + process.JetPlusTrackCorrections )

#-- Extra PAT collections -----------------------------------------------------
#include "PhysicsTools/PatAlgos/python/tools/jetTools.py"
from PhysicsTools.PatAlgos.tools.jetTools import *
if isFastSim:   switchJECSet(process, newName='Winter09', oldName='Summer08Redigi')
if True:
  addJetCollection(process, "iterativeCone5CaloJets", "IC5"
                                                    , doJTA             = True   # Run Jet-Track association & JetCharge
                                                    , doBTagging        = True   # Run b-tagging
                                                    , jetCorrLabel      = ("IC5", "Calo")
                                                    , doType1MET        = True
                                                    , genJetCollection  = cms.InputTag("iterativeCone5GenJets")
                                                    )
addJetCollection  (process, "iterativeCone5PFJets"  , 'IC5PF'
                                                    , runCleaner        = "PFJet"
                                                    , doJTA             = False  # Run Jet-Track association & JetCharge
                                                    , doBTagging        = True   # Run b-tagging
                                                    , jetCorrLabel      = ("IC5", "PF")
                                                    , doType1MET        = False
                                                    , genJetCollection  = cms.InputTag("iterativeCone5GenJets")
                                                    )
switchJetCollection(process, "sisCone5CaloJets"     , runCleaner        = "CaloJet"
                                                    , doJTA             = True   # Run Jet-Track association & JetCharge
                                                    , doBTagging        = True   # Run b-tagging
                                                    , jetCorrLabel      = ("SC5", "Calo")
                                                    , doType1MET        = True
                                                    , genJetCollection  = cms.InputTag("sisCone5GenJets")

                                                    )
#-- Jet Plus Track  -----------------------------------------------------
addJetCollection(process, "JetPlusTrackZSPCorJetIcone5", "IC5JPT"
                                                    , doJTA             = True   # Run Jet-Track association & JetCharge
                                                    , doBTagging        = True   # Run b-tagging
                                                    , jetCorrLabel      = None
                                                    , doType1MET        = True
                                                    , genJetCollection  = cms.InputTag("iterativeCone5GenJets")
                                                    )


#-- Particle flow MET is different from other MET collections  -------------------------------------
process.load("PhysicsTools.PFCandProducer.pfMET_cfi")
process.allLayer1METsPF = process.allLayer1METs.clone(
  metSource = cms.InputTag("pfMET"),
  addTrigMatch = cms.bool(False),
  addMuonCorrections = cms.bool(False),
)
process.patLayer0.replace( process.allLayer0METs, process.allLayer0METs + process.pfMET )
process.patLayer1.replace( process.allLayer1METs, process.allLayer1METs + process.allLayer1METsPF )

#-- tcMET ---------------------------------------------------------------------
process.load("RecoMET.METProducers.TCMET_cfi")
process.allLayer0METstcMET = cms.EDFilter("PATBaseMETCleaner",
    metSource = cms.InputTag('tcMet'), ## met corrected for jets and for muons
    markItems = cms.bool(True),    ## write the status flags in the output items
    bitsToIgnore = cms.vstring(),  ## You can specify some bit names,e.g. "Overflow/User1", "Core/Duplicate", "Isolation/All".
    saveRejected = cms.string(''), ## set this to a non empty label tosave the list of items which fail
    saveAll = cms.string(''),      ## set this to a non empty label tosave a list of all items both passing and failing
)
process.metTrigMatchHLT1MET65tcMET  = process.metTrigMatchHLT1MET65.clone (src       = cms.InputTag('allLayer0METstcMET'))
process.allLayer1METstcMET          = process.allLayer1METs.clone         (metSource = cms.InputTag('allLayer0METstcMET'), trigPrimMatch = cms.VInputTag(cms.InputTag("metTrigMatchHLT1MET65tcMET")))
process.selectedLayer1METstcMET     = process.selectedLayer1METs.clone    (src       = cms.InputTag('allLayer1METstcMET'))

process.tcMetSequence = cms.Sequence( process.allLayer0METstcMET
                                    * process.metTrigMatchHLT1MET65tcMET
                                    * process.allLayer1METstcMET
                                    * process.selectedLayer1METstcMET
                                    )


#-- Execution path ------------------------------------------------------------

# Re-name collections for uniformity
process.allLayer1JetsSC5        = process.allLayer1Jets
process.allLayer1METsSC5        = process.allLayer1METs
process.selectedLayer1Jets.src  = cms.InputTag("allLayer1JetsSC5")
process.selectedLayer1METs.src  = cms.InputTag("allLayer1METsSC5")
process.layer1Jets.replace(process.allLayer1Jets, process.allLayer1JetsSC5)
process.layer1METs.replace(process.allLayer1METs, process.allLayer1METsSC5)

process.patify    =  cms.Path( process.moreRecoJetMET )
if doPhotonID:
  process.patify *=  process.photonIDSequence
process.patify   *=( process.JPT
                   * process.patLayer0
                   * process.patLayer1
                   * process.tcMetSequence
                   )

#-- Output module configuration -----------------------------------------------
process.out         = cms.OutputModule("PoolOutputModule",
    fileName        = cms.untracked.string('patLayer1.root'),
    SelectEvents    = cms.untracked.PSet( SelectEvents = cms.vstring('patify') ),
    dropMetaDataForDroppedData  = cms.untracked.bool(True),
    outputCommands  = cms.untracked.vstring('drop *')
)
process.outpath     = cms.EndPath(process.out)
## Most of the following are inherited from 
##    process.load("PhysicsTools.PatAlgos.patLayer1_EventContent_cff")
##    process.out.outputCommands.extend(process.patLayer1EventContent.outputCommands)
## However we list them explicitly so as not to be confused by PAT version changes.
process.out.outputCommands.extend([ 'keep recoGenJets_iterativeCone5GenJets_*_*'
                                  , 'keep recoGenJets_sisCone5GenJets_*_*'
                                  , 'keep recoGenParticles_genParticles_*_*'
				  , 'keep recoGenMETs_*_*_*'
                                  , 'keep *_genEventProcID_*_*'
                                  , 'keep *_genEventScale_*_*'
                                  , 'keep *_genEventWeight_*_*'
                                  , 'keep *_genEventPdfInfo_*_*'
                                  , 'keep edmTriggerResults_TriggerResults_*_HLT'
                                  , 'keep *_hltTriggerSummaryAOD_*_*'
                                  , 'keep *_offlineBeamSpot_*_*'
                                  , 'keep *_offlinePrimaryVertices_*_*'
                                  , 'keep recoTracks_generalTracks_*_*'
                                  , 'keep *_towerMaker_*_'+process.name_()
                                  , 'keep *_allLayer1Photons_*_*'
                                  , 'keep *_allLayer1Electrons_*_*'
                                  , 'keep *_allLayer1Muons_*_*'
                                  , 'keep *_allLayer1Taus_*_*'
                                  , 'keep *_allLayer1Jets*_*_*'
                                  , 'keep *_allLayer1METs*_*_*'
                                  , 'keep *_allLayer1Hemispheres_*_*'
                                  , 'keep recoPFCandidates_*_*_*'
                                  , 'keep recoSuperClusters_corrected*_*_*'
                                  , 'keep recoTracks_*onversions_*_*'
                                  , 'keep *_PhotonIDProd_*_'+process.name_()
                                  , 'keep recoConversions_conversions_*_*'
                                  , 'keep recoTracks_*onversions_*_*'
                                  ])

import FWCore.ParameterSet.Config as cms
