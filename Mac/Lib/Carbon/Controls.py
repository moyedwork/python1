# Generated from 'Controls.h'

def FOUR_CHAR_CODE(x): return x
from Carbon.TextEdit import *
from Carbon.QuickDraw import *
from Carbon.Dragconst import *
from Carbon.CarbonEvents import *
from Carbon.Appearance import *
kDataBrowserItemAnyState = -1
kControlBevelButtonCenterPopupGlyphTag = -1
kDataBrowserClientPropertyFlagsMask = 0xFF000000

kControlDefProcType = FOUR_CHAR_CODE('CDEF')
kControlTemplateResourceType = FOUR_CHAR_CODE('CNTL')
kControlColorTableResourceType = FOUR_CHAR_CODE('cctb')
kControlDefProcResourceType = FOUR_CHAR_CODE('CDEF')
controlNotifyNothing = FOUR_CHAR_CODE('nada')
controlNotifyClick = FOUR_CHAR_CODE('clik')
controlNotifyFocus = FOUR_CHAR_CODE('focu')
controlNotifyKey = FOUR_CHAR_CODE('key ') 
kControlCanAutoInvalidate = 1L << 0 
staticTextProc = 256
editTextProc = 272
iconProc = 288
userItemProc = 304
pictItemProc = 320   
cFrameColor = 0
cBodyColor = 1
cTextColor = 2
cThumbColor = 3
kNumberCtlCTabEntries = 4
kControlNoVariant = 0
kControlUsesOwningWindowsFontVariant = 1 << 3 
kControlNoPart = 0
kControlIndicatorPart = 129
kControlDisabledPart = 254
kControlInactivePart = 255
kControlEntireControl = 0
kControlStructureMetaPart = -1
kControlContentMetaPart = -2
kControlFocusNoPart = 0
kControlFocusNextPart = -1
kControlFocusPrevPart = -2    
kControlCollectionTagBounds = FOUR_CHAR_CODE('boun')
kControlCollectionTagValue = FOUR_CHAR_CODE('valu')
kControlCollectionTagMinimum = FOUR_CHAR_CODE('min ')
kControlCollectionTagMaximum = FOUR_CHAR_CODE('max ')
kControlCollectionTagViewSize = FOUR_CHAR_CODE('view')
kControlCollectionTagVisibility = FOUR_CHAR_CODE('visi')
kControlCollectionTagRefCon = FOUR_CHAR_CODE('refc')
kControlCollectionTagTitle = FOUR_CHAR_CODE('titl')
kControlCollectionTagUnicodeTitle = FOUR_CHAR_CODE('uttl')
kControlCollectionTagIDSignature = FOUR_CHAR_CODE('idsi')
kControlCollectionTagIDID = FOUR_CHAR_CODE('idid')
kControlCollectionTagCommand = FOUR_CHAR_CODE('cmd ')
kControlCollectionTagVarCode = FOUR_CHAR_CODE('varc') 
kControlCollectionTagSubControls = FOUR_CHAR_CODE('subc') 
kControlContentTextOnly = 0
kControlNoContent = 0
kControlContentIconSuiteRes = 1
kControlContentCIconRes = 2
kControlContentPictRes = 3
kControlContentICONRes = 4
kControlContentIconSuiteHandle = 129
kControlContentCIconHandle = 130
kControlContentPictHandle = 131
kControlContentIconRef = 132
kControlContentICON = 133
kControlKeyScriptBehaviorAllowAnyScript = FOUR_CHAR_CODE('any ')
kControlKeyScriptBehaviorPrefersRoman = FOUR_CHAR_CODE('prmn')
kControlKeyScriptBehaviorRequiresRoman = FOUR_CHAR_CODE('rrmn') 
kControlFontBigSystemFont = -1
kControlFontSmallSystemFont = -2
kControlFontSmallBoldSystemFont = -3
kControlFontViewSystemFont = -4    
kControlUseFontMask = 0x0001
kControlUseFaceMask = 0x0002
kControlUseSizeMask = 0x0004
kControlUseForeColorMask = 0x0008
kControlUseBackColorMask = 0x0010
kControlUseModeMask = 0x0020
kControlUseJustMask = 0x0040
kControlUseAllMask = 0x00FF
kControlAddFontSizeMask = 0x0100
kControlAddToMetaFontMask = 0x0200 
kControlUseThemeFontIDMask = 0x0080 
kDoNotActivateAndIgnoreClick = 0
kDoNotActivateAndHandleClick = 1
kActivateAndIgnoreClick = 2
kActivateAndHandleClick = 3     
kControlFontStyleTag = FOUR_CHAR_CODE('font')
kControlKeyFilterTag = FOUR_CHAR_CODE('fltr')
kControlKindTag = FOUR_CHAR_CODE('kind')
kControlSizeTag = FOUR_CHAR_CODE('size')
kControlSupportsGhosting = 1 << 0
kControlSupportsEmbedding = 1 << 1
kControlSupportsFocus = 1 << 2
kControlWantsIdle = 1 << 3
kControlWantsActivate = 1 << 4
kControlHandlesTracking = 1 << 5
kControlSupportsDataAccess = 1 << 6
kControlHasSpecialBackground = 1 << 7
kControlGetsFocusOnClick = 1 << 8
kControlSupportsCalcBestRect = 1 << 9
kControlSupportsLiveFeedback = 1 << 10
kControlHasRadioBehavior = 1 << 11
kControlSupportsDragAndDrop = 1 << 12
kControlAutoToggles = 1 << 14
kControlSupportsGetRegion = 1 << 17
kControlSupportsFlattening = 1 << 19
kControlSupportsSetCursor = 1 << 20
kControlSupportsContextualMenus = 1 << 21
kControlSupportsClickActivation = 1 << 22
kControlIdlesWithTimer = 1 << 23 
drawCntl = 0
testCntl = 1
calcCRgns = 2
initCntl = 3
dispCntl = 4
posCntl = 5
thumbCntl = 6
dragCntl = 7
autoTrack = 8
calcCntlRgn = 10
calcThumbRgn = 11
drawThumbOutline = 12
kControlMsgDrawGhost = 13
kControlMsgCalcBestRect = 14
kControlMsgHandleTracking = 15
kControlMsgFocus = 16
kControlMsgKeyDown = 17
kControlMsgIdle = 18
kControlMsgGetFeatures = 19
kControlMsgSetData = 20
kControlMsgGetData = 21
kControlMsgActivate = 22
kControlMsgSetUpBackground = 23
kControlMsgCalcValueFromPos = 26
kControlMsgTestNewMsgSupport = 27
kControlMsgSubValueChanged = 25
kControlMsgSubControlAdded = 28
kControlMsgSubControlRemoved = 29
kControlMsgApplyTextColor = 30
kControlMsgGetRegion = 31
kControlMsgFlatten = 32
kControlMsgSetCursor = 33
kControlMsgDragEnter = 38
kControlMsgDragLeave = 39
kControlMsgDragWithin = 40
kControlMsgDragReceive = 41
kControlMsgDisplayDebugInfo = 46
kControlMsgContextualMenuClick = 47
kControlMsgGetClickActivation = 48    
kControlSizeNormal = 0
kControlSizeSmall = 1
kControlSizeLarge = 2
kControlSizeAuto = 0xFFFF
kDrawControlEntireControl = 0
kDrawControlIndicatorOnly = 129
kDragControlEntireControl = 0
kDragControlIndicator = 1
kControlSupportsNewMessages = FOUR_CHAR_CODE(' ok ')
kControlKeyFilterBlockKey = 0
kControlKeyFilterPassKey = 1
noConstraint = kNoConstraint
hAxisOnly = 1
vAxisOnly = 2
kControlDefProcPtr = 0
kControlDefObjectClass = 1     
kControlKindSignatureApple = FOUR_CHAR_CODE('appl')
kControlPropertyPersistent = 0x00000001 
kDragTrackingEnterControl = 2
kDragTrackingInControl = 3
kDragTrackingLeaveControl = 4
useWFont = kControlUsesOwningWindowsFontVariant
inThumb = kControlIndicatorPart
kNoHiliteControlPart = kControlNoPart
kInIndicatorControlPart = kControlIndicatorPart
kReservedControlPart = kControlDisabledPart
kControlInactiveControlPart = kControlInactivePart
kControlTabListResType = FOUR_CHAR_CODE('tab#')
kControlListDescResType = FOUR_CHAR_CODE('ldes') 
kControlCheckBoxUncheckedValue = 0
kControlCheckBoxCheckedValue = 1
kControlCheckBoxMixedValue = 2
kControlRadioButtonUncheckedValue = 0
kControlRadioButtonCheckedValue = 1
kControlRadioButtonMixedValue = 2
popupFixedWidth = 1 << 0
popupVariableWidth = 1 << 1
popupUseAddResMenu = 1 << 2
popupUseWFont = 1 << 3
popupTitleBold = 1 << 8
popupTitleItalic = 1 << 9
popupTitleUnderline = 1 << 10
popupTitleOutline = 1 << 11
popupTitleShadow = 1 << 12
popupTitleCondense = 1 << 13
popupTitleExtend = 1 << 14
popupTitleNoStyle = 1 << 15
popupTitleLeftJust = 0x00000000
popupTitleCenterJust = 0x00000001
popupTitleRightJust = 0x000000FF
pushButProc = 0
checkBoxProc = 1
radioButProc = 2
scrollBarProc = 16
popupMenuProc = 1008
kControlLabelPart = 1
kControlMenuPart = 2
kControlTrianglePart = 4
kControlEditTextPart = 5
kControlPicturePart = 6
kControlIconPart = 7
kControlClockPart = 8
kControlListBoxPart = 24
kControlListBoxDoubleClickPart = 25
kControlImageWellPart = 26
kControlRadioGroupPart = 27
kControlButtonPart = 10
kControlCheckBoxPart = 11
kControlRadioButtonPart = 11
kControlUpButtonPart = 20
kControlDownButtonPart = 21
kControlPageUpPart = 22
kControlPageDownPart = 23
kControlClockHourDayPart = 9
kControlClockMinuteMonthPart = 10
kControlClockSecondYearPart = 11
kControlClockAMPMPart = 12
kControlDataBrowserPart = 24
kControlDataBrowserDraggedPart = 25   
kControlBevelButtonSmallBevelProc = 32
kControlBevelButtonNormalBevelProc = 33
kControlBevelButtonLargeBevelProc = 34
kControlBevelButtonSmallBevelVariant = 0
kControlBevelButtonNormalBevelVariant = (1 << 0)
kControlBevelButtonLargeBevelVariant = (1 << 1)
kControlBevelButtonMenuOnRightVariant = (1 << 2)
kControlBevelButtonSmallBevel = 0
kControlBevelButtonNormalBevel = 1
kControlBevelButtonLargeBevel = 2
kControlBehaviorPushbutton = 0
kControlBehaviorToggles = 0x0100
kControlBehaviorSticky = 0x0200
kControlBehaviorSingleValueMenu = 0
kControlBehaviorMultiValueMenu = 0x4000
kControlBehaviorOffsetContents = 0x8000
kControlBehaviorCommandMenu = 0x2000 
kControlBevelButtonMenuOnBottom = 0
kControlBevelButtonMenuOnRight = (1 << 2)
kControlKindBevelButton = FOUR_CHAR_CODE('bevl')
kControlBevelButtonAlignSysDirection = -1
kControlBevelButtonAlignCenter = 0
kControlBevelButtonAlignLeft = 1
kControlBevelButtonAlignRight = 2
kControlBevelButtonAlignTop = 3
kControlBevelButtonAlignBottom = 4
kControlBevelButtonAlignTopLeft = 5
kControlBevelButtonAlignBottomLeft = 6
kControlBevelButtonAlignTopRight = 7
kControlBevelButtonAlignBottomRight = 8
kControlBevelButtonAlignTextSysDirection = teFlushDefault
kControlBevelButtonAlignTextCenter = teCenter
kControlBevelButtonAlignTextFlushRight = teFlushRight
kControlBevelButtonAlignTextFlushLeft = teFlushLeft
kControlBevelButtonPlaceSysDirection = -1
kControlBevelButtonPlaceNormally = 0
kControlBevelButtonPlaceToRightOfGraphic = 1
kControlBevelButtonPlaceToLeftOfGraphic = 2
kControlBevelButtonPlaceBelowGraphic = 3
kControlBevelButtonPlaceAboveGraphic = 4
kControlBevelButtonContentTag = FOUR_CHAR_CODE('cont')
kControlBevelButtonTransformTag = FOUR_CHAR_CODE('tran')
kControlBevelButtonTextAlignTag = FOUR_CHAR_CODE('tali')
kControlBevelButtonTextOffsetTag = FOUR_CHAR_CODE('toff')
kControlBevelButtonGraphicAlignTag = FOUR_CHAR_CODE('gali')
kControlBevelButtonGraphicOffsetTag = FOUR_CHAR_CODE('goff')
kControlBevelButtonTextPlaceTag = FOUR_CHAR_CODE('tplc')
kControlBevelButtonMenuValueTag = FOUR_CHAR_CODE('mval')
kControlBevelButtonMenuHandleTag = FOUR_CHAR_CODE('mhnd')
kControlBevelButtonMenuRefTag = FOUR_CHAR_CODE('mhnd')
kControlBevelButtonOwnedMenuRefTag = FOUR_CHAR_CODE('omrf')
# kControlBevelButtonCenterPopupGlyphTag = FOUR_CHAR_CODE('pglc')
kControlBevelButtonKindTag = FOUR_CHAR_CODE('bebk') 
kControlBevelButtonLastMenuTag = FOUR_CHAR_CODE('lmnu')
kControlBevelButtonMenuDelayTag = FOUR_CHAR_CODE('mdly') 
kControlBevelButtonScaleIconTag = FOUR_CHAR_CODE('scal') 
kControlSliderProc = 48
kControlSliderLiveFeedback = (1 << 0)
kControlSliderHasTickMarks = (1 << 1)
kControlSliderReverseDirection = (1 << 2)
kControlSliderNonDirectional = (1 << 3)
kControlSliderPointsDownOrRight = 0
kControlSliderPointsUpOrLeft = 1
kControlSliderDoesNotPoint = 2
kControlKindSlider = FOUR_CHAR_CODE('sldr')
kControlTriangleProc = 64
kControlTriangleLeftFacingProc = 65
kControlTriangleAutoToggleProc = 66
kControlTriangleLeftFacingAutoToggleProc = 67
kControlDisclosureTrianglePointDefault = 0
kControlDisclosureTrianglePointRight = 1
kControlDisclosureTrianglePointLeft = 2
kControlKindDisclosureTriangle = FOUR_CHAR_CODE('dist')
kControlTriangleLastValueTag = FOUR_CHAR_CODE('last') 
kControlProgressBarProc = 80
kControlRelevanceBarProc = 81
kControlKindProgressBar = FOUR_CHAR_CODE('prgb')
kControlKindRelevanceBar = FOUR_CHAR_CODE('relb')
kControlProgressBarIndeterminateTag = FOUR_CHAR_CODE('inde')
kControlProgressBarAnimatingTag = FOUR_CHAR_CODE('anim') 
kControlLittleArrowsProc = 96
kControlKindLittleArrows = FOUR_CHAR_CODE('larr')
kControlChasingArrowsProc = 112
kControlKindChasingArrows = FOUR_CHAR_CODE('carr')
kControlChasingArrowsAnimatingTag = FOUR_CHAR_CODE('anim') 
kControlTabLargeProc = 128
kControlTabSmallProc = 129
kControlTabLargeNorthProc = 128
kControlTabSmallNorthProc = 129
kControlTabLargeSouthProc = 130
kControlTabSmallSouthProc = 131
kControlTabLargeEastProc = 132
kControlTabSmallEastProc = 133
kControlTabLargeWestProc = 134
kControlTabSmallWestProc = 135   
kControlTabDirectionNorth = 0
kControlTabDirectionSouth = 1
kControlTabDirectionEast = 2
kControlTabDirectionWest = 3
kControlTabSizeLarge = kControlSizeNormal
kControlTabSizeSmall = kControlSizeSmall
kControlKindTabs = FOUR_CHAR_CODE('tabs')
kControlTabContentRectTag = FOUR_CHAR_CODE('rect')
kControlTabEnabledFlagTag = FOUR_CHAR_CODE('enab')
kControlTabFontStyleTag = kControlFontStyleTag 
kControlTabInfoTag = FOUR_CHAR_CODE('tabi') 
kControlTabImageContentTag = FOUR_CHAR_CODE('cont') 
kControlTabInfoVersionZero = 0
kControlTabInfoVersionOne = 1     
kControlSeparatorLineProc = 144
kControlKindSeparator = FOUR_CHAR_CODE('sepa')
kControlGroupBoxTextTitleProc = 160
kControlGroupBoxCheckBoxProc = 161
kControlGroupBoxPopupButtonProc = 162
kControlGroupBoxSecondaryTextTitleProc = 164
kControlGroupBoxSecondaryCheckBoxProc = 165
kControlGroupBoxSecondaryPopupButtonProc = 166
kControlKindGroupBox = FOUR_CHAR_CODE('grpb')
kControlKindCheckGroupBox = FOUR_CHAR_CODE('cgrp')
kControlKindPopupGroupBox = FOUR_CHAR_CODE('pgrp')
kControlGroupBoxMenuHandleTag = FOUR_CHAR_CODE('mhan')
kControlGroupBoxMenuRefTag = FOUR_CHAR_CODE('mhan')
kControlGroupBoxFontStyleTag = kControlFontStyleTag 
kControlGroupBoxTitleRectTag = FOUR_CHAR_CODE('trec') 
kControlImageWellProc = 176
kControlKindImageWell = FOUR_CHAR_CODE('well')
kControlImageWellContentTag = FOUR_CHAR_CODE('cont')
kControlImageWellTransformTag = FOUR_CHAR_CODE('tran')
kControlImageWellIsDragDestinationTag = FOUR_CHAR_CODE('drag') 
kControlPopupArrowEastProc = 192
kControlPopupArrowWestProc = 193
kControlPopupArrowNorthProc = 194
kControlPopupArrowSouthProc = 195
kControlPopupArrowSmallEastProc = 196
kControlPopupArrowSmallWestProc = 197
kControlPopupArrowSmallNorthProc = 198
kControlPopupArrowSmallSouthProc = 199
kControlPopupArrowOrientationEast = 0
kControlPopupArrowOrientationWest = 1
kControlPopupArrowOrientationNorth = 2
kControlPopupArrowOrientationSouth = 3
kControlPopupArrowSizeNormal = 0
kControlPopupArrowSizeSmall = 1
kControlKindPopupArrow = FOUR_CHAR_CODE('parr')
kControlPlacardProc = 224
kControlKindPlacard = FOUR_CHAR_CODE('plac')
kControlClockTimeProc = 240
kControlClockTimeSecondsProc = 241
kControlClockDateProc = 242
kControlClockMonthYearProc = 243
kControlClockTypeHourMinute = 0
kControlClockTypeHourMinuteSecond = 1
kControlClockTypeMonthDayYear = 2
kControlClockTypeMonthYear = 3
kControlClockFlagStandard = 0
kControlClockNoFlags = 0
kControlClockFlagDisplayOnly = 1
kControlClockIsDisplayOnly = 1
kControlClockFlagLive = 2
kControlClockIsLive = 2
kControlKindClock = FOUR_CHAR_CODE('clck')
kControlClockLongDateTag = FOUR_CHAR_CODE('date')
kControlClockFontStyleTag = kControlFontStyleTag
kControlClockAnimatingTag = FOUR_CHAR_CODE('anim') 
kControlUserPaneProc = 256
kControlKindUserPane = FOUR_CHAR_CODE('upan')
kControlUserItemDrawProcTag = FOUR_CHAR_CODE('uidp')
kControlUserPaneDrawProcTag = FOUR_CHAR_CODE('draw')
kControlUserPaneHitTestProcTag = FOUR_CHAR_CODE('hitt')
kControlUserPaneTrackingProcTag = FOUR_CHAR_CODE('trak')
kControlUserPaneIdleProcTag = FOUR_CHAR_CODE('idle')
kControlUserPaneKeyDownProcTag = FOUR_CHAR_CODE('keyd')
kControlUserPaneActivateProcTag = FOUR_CHAR_CODE('acti')
kControlUserPaneFocusProcTag = FOUR_CHAR_CODE('foci')
kControlUserPaneBackgroundProcTag = FOUR_CHAR_CODE('back') 
kControlEditTextProc = 272
kControlEditTextPasswordProc = 274
kControlEditTextInlineInputProc = 276 
kControlKindEditText = FOUR_CHAR_CODE('etxt')
kControlEditTextStyleTag = kControlFontStyleTag
kControlEditTextTextTag = FOUR_CHAR_CODE('text')
kControlEditTextTEHandleTag = FOUR_CHAR_CODE('than')
kControlEditTextKeyFilterTag = kControlKeyFilterTag
kControlEditTextSelectionTag = FOUR_CHAR_CODE('sele')
kControlEditTextPasswordTag = FOUR_CHAR_CODE('pass') 
kControlEditTextKeyScriptBehaviorTag = FOUR_CHAR_CODE('kscr')
kControlEditTextLockedTag = FOUR_CHAR_CODE('lock')
kControlEditTextFixedTextTag = FOUR_CHAR_CODE('ftxt')
kControlEditTextValidationProcTag = FOUR_CHAR_CODE('vali')
kControlEditTextInlinePreUpdateProcTag = FOUR_CHAR_CODE('prup')
kControlEditTextInlinePostUpdateProcTag = FOUR_CHAR_CODE('poup') 
kControlEditTextCFStringTag = FOUR_CHAR_CODE('cfst') 
kControlStaticTextProc = 288
kControlKindStaticText = FOUR_CHAR_CODE('stxt')
kControlStaticTextStyleTag = kControlFontStyleTag
kControlStaticTextTextTag = FOUR_CHAR_CODE('text')
kControlStaticTextTextHeightTag = FOUR_CHAR_CODE('thei') 
kControlStaticTextTruncTag = FOUR_CHAR_CODE('trun') 
kControlStaticTextCFStringTag = FOUR_CHAR_CODE('cfst') 
kControlPictureProc = 304
kControlPictureNoTrackProc = 305   
kControlKindPicture = FOUR_CHAR_CODE('pict')
kControlPictureHandleTag = FOUR_CHAR_CODE('pich') 
kControlIconProc = 320
kControlIconNoTrackProc = 321
kControlIconSuiteProc = 322
kControlIconSuiteNoTrackProc = 323   
kControlIconRefProc = 324
kControlIconRefNoTrackProc = 325   
kControlKindIcon = FOUR_CHAR_CODE('icon')
kControlIconTransformTag = FOUR_CHAR_CODE('trfm')
kControlIconAlignmentTag = FOUR_CHAR_CODE('algn') 
kControlIconResourceIDTag = FOUR_CHAR_CODE('ires')
kControlIconContentTag = FOUR_CHAR_CODE('cont') 
kControlWindowHeaderProc = 336
kControlWindowListViewHeaderProc = 337 
kControlKindWindowHeader = FOUR_CHAR_CODE('whed')
kControlListBoxProc = 352
kControlListBoxAutoSizeProc = 353
kControlKindListBox = FOUR_CHAR_CODE('lbox')
kControlListBoxListHandleTag = FOUR_CHAR_CODE('lhan')
kControlListBoxKeyFilterTag = kControlKeyFilterTag
kControlListBoxFontStyleTag = kControlFontStyleTag 
kControlListBoxDoubleClickTag = FOUR_CHAR_CODE('dblc')
kControlListBoxLDEFTag = FOUR_CHAR_CODE('ldef') 
kControlPushButtonProc = 368
kControlCheckBoxProc = 369
kControlRadioButtonProc = 370
kControlPushButLeftIconProc = 374
kControlPushButRightIconProc = 375   
kControlCheckBoxAutoToggleProc = 371
kControlRadioButtonAutoToggleProc = 372
kControlPushButtonIconOnLeft = 6
kControlPushButtonIconOnRight = 7
kControlKindPushButton = FOUR_CHAR_CODE('push')
kControlKindPushIconButton = FOUR_CHAR_CODE('picn')
kControlKindRadioButton = FOUR_CHAR_CODE('rdio')
kControlKindCheckBox = FOUR_CHAR_CODE('cbox')
kControlPushButtonDefaultTag = FOUR_CHAR_CODE('dflt')
kControlPushButtonCancelTag = FOUR_CHAR_CODE('cncl') 
kControlScrollBarProc = 384
kControlScrollBarLiveProc = 386   
kControlKindScrollBar = FOUR_CHAR_CODE('sbar')
kControlScrollBarShowsArrowsTag = FOUR_CHAR_CODE('arro') 
kControlPopupButtonProc = 400
kControlPopupFixedWidthVariant = 1 << 0
kControlPopupVariableWidthVariant = 1 << 1
kControlPopupUseAddResMenuVariant = 1 << 2
kControlPopupUseWFontVariant = kControlUsesOwningWindowsFontVariant
kControlKindPopupButton = FOUR_CHAR_CODE('popb')
kControlPopupButtonMenuHandleTag = FOUR_CHAR_CODE('mhan')
kControlPopupButtonMenuRefTag = FOUR_CHAR_CODE('mhan')
kControlPopupButtonMenuIDTag = FOUR_CHAR_CODE('mnid') 
kControlPopupButtonExtraHeightTag = FOUR_CHAR_CODE('exht')
kControlPopupButtonOwnedMenuRefTag = FOUR_CHAR_CODE('omrf')
kControlPopupButtonCheckCurrentTag = FOUR_CHAR_CODE('chck') 
kControlRadioGroupProc = 416
kControlKindRadioGroup = FOUR_CHAR_CODE('rgrp')
kControlScrollTextBoxProc = 432
kControlScrollTextBoxAutoScrollProc = 433
kControlKindScrollingTextBox = FOUR_CHAR_CODE('stbx')
kControlScrollTextBoxDelayBeforeAutoScrollTag = FOUR_CHAR_CODE('stdl')
kControlScrollTextBoxDelayBetweenAutoScrollTag = FOUR_CHAR_CODE('scdl')
kControlScrollTextBoxAutoScrollAmountTag = FOUR_CHAR_CODE('samt')
kControlScrollTextBoxContentsTag = FOUR_CHAR_CODE('tres')
kControlScrollTextBoxAnimatingTag = FOUR_CHAR_CODE('anim') 
kControlKindDisclosureButton = FOUR_CHAR_CODE('disb')
kControlDisclosureButtonClosed = 0
kControlDisclosureButtonDisclosed = 1
kControlRoundButtonNormalSize = kControlSizeNormal
kControlRoundButtonLargeSize = kControlSizeLarge
kControlRoundButtonContentTag = FOUR_CHAR_CODE('cont')
kControlRoundButtonSizeTag = FOUR_CHAR_CODE('size') 
kControlKindRoundButton = FOUR_CHAR_CODE('rndb')
kControlKindDataBrowser = FOUR_CHAR_CODE('datb')
errDataBrowserNotConfigured = -4970
errDataBrowserItemNotFound = -4971
errDataBrowserItemNotAdded = -4975
errDataBrowserPropertyNotFound = -4972
errDataBrowserInvalidPropertyPart = -4973
errDataBrowserInvalidPropertyData = -4974
errDataBrowserPropertyNotSupported = -4979 
kControlDataBrowserIncludesFrameAndFocusTag = FOUR_CHAR_CODE('brdr')
kControlDataBrowserKeyFilterTag = kControlEditTextKeyFilterTag
kControlDataBrowserEditTextKeyFilterTag = kControlDataBrowserKeyFilterTag
kControlDataBrowserEditTextValidationProcTag = kControlEditTextValidationProcTag
kDataBrowserNoView = 0x3F3F3F3F
kDataBrowserListView = FOUR_CHAR_CODE('lstv')
kDataBrowserColumnView = FOUR_CHAR_CODE('clmv')
kDataBrowserDragSelect = 1 << 0
kDataBrowserSelectOnlyOne = 1 << 1
kDataBrowserResetSelection = 1 << 2
kDataBrowserCmdTogglesSelection = 1 << 3
kDataBrowserNoDisjointSelection = 1 << 4
kDataBrowserAlwaysExtendSelection = 1 << 5
kDataBrowserNeverEmptySelectionSet = 1 << 6 
kDataBrowserOrderUndefined = 0
kDataBrowserOrderIncreasing = 1
kDataBrowserOrderDecreasing = 2
kDataBrowserNoItem = 0L    
kDataBrowserItemNoState = 0
# kDataBrowserItemAnyState = (unsigned long)(-1)
kDataBrowserItemIsSelected = 1 << 0
kDataBrowserContainerIsOpen = 1 << 1
kDataBrowserItemIsDragTarget = 1 << 2 
kDataBrowserRevealOnly = 0
kDataBrowserRevealAndCenterInView = 1 << 0
kDataBrowserRevealWithoutSelecting = 1 << 1
kDataBrowserItemsAdd = 0
kDataBrowserItemsAssign = 1
kDataBrowserItemsToggle = 2
kDataBrowserItemsRemove = 3     
kDataBrowserSelectionAnchorUp = 0
kDataBrowserSelectionAnchorDown = 1
kDataBrowserSelectionAnchorLeft = 2
kDataBrowserSelectionAnchorRight = 3
kDataBrowserEditMsgUndo = kHICommandUndo
kDataBrowserEditMsgRedo = kHICommandRedo
kDataBrowserEditMsgCut = kHICommandCut
kDataBrowserEditMsgCopy = kHICommandCopy
kDataBrowserEditMsgPaste = kHICommandPaste
kDataBrowserEditMsgClear = kHICommandClear
kDataBrowserEditMsgSelectAll = kHICommandSelectAll
kDataBrowserItemAdded = 1
kDataBrowserItemRemoved = 2
kDataBrowserEditStarted = 3
kDataBrowserEditStopped = 4
kDataBrowserItemSelected = 5
kDataBrowserItemDeselected = 6
kDataBrowserItemDoubleClicked = 7
kDataBrowserContainerOpened = 8
kDataBrowserContainerClosing = 9
kDataBrowserContainerClosed = 10
kDataBrowserContainerSorting = 11
kDataBrowserContainerSorted = 12
kDataBrowserUserToggledContainer = 16
kDataBrowserTargetChanged = 15
kDataBrowserUserStateChanged = 13
kDataBrowserSelectionSetChanged = 14  
kDataBrowserItemNoProperty = 0L
kDataBrowserItemIsActiveProperty = 1L
kDataBrowserItemIsSelectableProperty = 2L
kDataBrowserItemIsEditableProperty = 3L
kDataBrowserItemIsContainerProperty = 4L
kDataBrowserContainerIsOpenableProperty = 5L
kDataBrowserContainerIsClosableProperty = 6L
kDataBrowserContainerIsSortableProperty = 7L
kDataBrowserItemSelfIdentityProperty = 8L
kDataBrowserContainerAliasIDProperty = 9L
kDataBrowserColumnViewPreviewProperty = 10L
kDataBrowserItemParentContainerProperty = 11L 
kDataBrowserCustomType = 0x3F3F3F3F
kDataBrowserIconType = FOUR_CHAR_CODE('icnr')
kDataBrowserTextType = FOUR_CHAR_CODE('text')
kDataBrowserDateTimeType = FOUR_CHAR_CODE('date')
kDataBrowserSliderType = FOUR_CHAR_CODE('sldr')
kDataBrowserCheckboxType = FOUR_CHAR_CODE('chbx')
kDataBrowserProgressBarType = FOUR_CHAR_CODE('prog')
kDataBrowserRelevanceRankType = FOUR_CHAR_CODE('rank')
kDataBrowserPopupMenuType = FOUR_CHAR_CODE('menu')
kDataBrowserIconAndTextType = FOUR_CHAR_CODE('ticn') 
kDataBrowserPropertyEnclosingPart = 0L
kDataBrowserPropertyContentPart = FOUR_CHAR_CODE('----')
kDataBrowserPropertyDisclosurePart = FOUR_CHAR_CODE('disc')
kDataBrowserPropertyTextPart = kDataBrowserTextType
kDataBrowserPropertyIconPart = kDataBrowserIconType
kDataBrowserPropertySliderPart = kDataBrowserSliderType
kDataBrowserPropertyCheckboxPart = kDataBrowserCheckboxType
kDataBrowserPropertyProgressBarPart = kDataBrowserProgressBarType
kDataBrowserPropertyRelevanceRankPart = kDataBrowserRelevanceRankType
kDataBrowserUniversalPropertyFlagsMask = 0xFF
kDataBrowserPropertyIsMutable = 1 << 0
kDataBrowserDefaultPropertyFlags = 0 << 0
kDataBrowserUniversalPropertyFlags = kDataBrowserUniversalPropertyFlagsMask
kDataBrowserPropertyIsEditable = kDataBrowserPropertyIsMutable 
kDataBrowserPropertyFlagsOffset = 8
kDataBrowserPropertyFlagsMask = 0xFF << kDataBrowserPropertyFlagsOffset
kDataBrowserCheckboxTriState = 1 << kDataBrowserPropertyFlagsOffset
kDataBrowserDateTimeRelative = 1 << (kDataBrowserPropertyFlagsOffset)
kDataBrowserDateTimeDateOnly = 1 << (kDataBrowserPropertyFlagsOffset + 1)
kDataBrowserDateTimeTimeOnly = 1 << (kDataBrowserPropertyFlagsOffset + 2)
kDataBrowserDateTimeSecondsToo = 1 << (kDataBrowserPropertyFlagsOffset + 3)
kDataBrowserSliderPlainThumb = kThemeThumbPlain << kDataBrowserPropertyFlagsOffset
kDataBrowserSliderUpwardThumb = kThemeThumbUpward << kDataBrowserPropertyFlagsOffset
kDataBrowserSliderDownwardThumb = kThemeThumbDownward << kDataBrowserPropertyFlagsOffset
kDataBrowserDoNotTruncateText = 3 << kDataBrowserPropertyFlagsOffset
kDataBrowserTruncateTextAtEnd = 2 << kDataBrowserPropertyFlagsOffset
kDataBrowserTruncateTextMiddle = 0 << kDataBrowserPropertyFlagsOffset
kDataBrowserTruncateTextAtStart = 1 << kDataBrowserPropertyFlagsOffset
kDataBrowserPropertyModificationFlags = kDataBrowserPropertyFlagsMask
kDataBrowserRelativeDateTime = kDataBrowserDateTimeRelative 
kDataBrowserViewSpecificFlagsOffset = 16
kDataBrowserViewSpecificFlagsMask = 0xFF << kDataBrowserViewSpecificFlagsOffset
kDataBrowserViewSpecificPropertyFlags = kDataBrowserViewSpecificFlagsMask 
kDataBrowserClientPropertyFlagsOffset = 24
# kDataBrowserClientPropertyFlagsMask = (unsigned long)(0xFF << kDataBrowserClientPropertyFlagsOffset)
kDataBrowserLatestCallbacks = 0
kDataBrowserContentHit = 1
kDataBrowserNothingHit = 0
kDataBrowserStopTracking = -1
kDataBrowserLatestCustomCallbacks = 0
kDataBrowserTableViewMinimalHilite = 0
kDataBrowserTableViewFillHilite = 1
kDataBrowserTableViewSelectionColumn = 1 << kDataBrowserViewSpecificFlagsOffset
kDataBrowserTableViewLastColumn = -1
kDataBrowserListViewMovableColumn = 1 << (kDataBrowserViewSpecificFlagsOffset + 1)
kDataBrowserListViewSortableColumn = 1 << (kDataBrowserViewSpecificFlagsOffset + 2)
kDataBrowserListViewSelectionColumn = kDataBrowserTableViewSelectionColumn
kDataBrowserListViewDefaultColumnFlags = kDataBrowserListViewMovableColumn + kDataBrowserListViewSortableColumn
kDataBrowserListViewLatestHeaderDesc = 0
kDataBrowserListViewAppendColumn = kDataBrowserTableViewLastColumn
kControlEditUnicodeTextPostUpdateProcTag = FOUR_CHAR_CODE('upup')
kControlEditUnicodeTextProc = 912
kControlEditUnicodeTextPasswordProc = 914
kControlCheckboxUncheckedValue = kControlCheckBoxUncheckedValue
kControlCheckboxCheckedValue = kControlCheckBoxCheckedValue
kControlCheckboxMixedValue = kControlCheckBoxMixedValue
inLabel = kControlLabelPart
inMenu = kControlMenuPart
inTriangle = kControlTrianglePart
inButton = kControlButtonPart
inCheckBox = kControlCheckBoxPart
inUpButton = kControlUpButtonPart
inDownButton = kControlDownButtonPart
inPageUp = kControlPageUpPart
inPageDown = kControlPageDownPart
kInLabelControlPart = kControlLabelPart
kInMenuControlPart = kControlMenuPart
kInTriangleControlPart = kControlTrianglePart
kInButtonControlPart = kControlButtonPart
kInCheckBoxControlPart = kControlCheckBoxPart
kInUpButtonControlPart = kControlUpButtonPart
kInDownButtonControlPart = kControlDownButtonPart
kInPageUpControlPart = kControlPageUpPart
kInPageDownControlPart = kControlPageDownPart
