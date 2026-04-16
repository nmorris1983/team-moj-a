//
// For guidance on how to create routes see:
// https://prototype-kit.service.gov.uk/docs/create-routes
//

const govukPrototypeKit = require('govuk-prototype-kit')
const router = govukPrototypeKit.requests.setupRouter()

// Load JSON data
const cases = require('./data/cases.json')
const policies = require('./data/policies.json')
const workflows = require('./data/workflows.json')
const decisionTemplates = require('./data/decision-templates.json')
const correspondenceTemplates = require('./data/correspondence-templates.json')
const precedents = require('./data/precedents.json')
const qualityChecklists = require('./data/quality-checklists.json')

// Load AI-generated summaries (produced by ai_summary/main.py)
let aiNotes = []
try {
  aiNotes = require('../data/ai_notes.json')
} catch (e) {
  console.warn('ai_notes.json not found — run ai_summary/main.py to generate it')
}

// Helper: get status tag colour
function statusTagClass (status) {
  const map = {
    'New': 'govuk-tag--blue',
    'In progress': '',
    'Awaiting evidence': 'govuk-tag--yellow',
    'Ready for decision': 'govuk-tag--green',
    'Decision made': 'govuk-tag--grey',
    'Escalated': 'govuk-tag--red',
    'Closed': 'govuk-tag--grey'
  }
  return map[status] || ''
}

// Helper: get deadline tag info
function deadlineTag (deadlineStr) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const deadline = parseGovDate(deadlineStr)
  if (!deadline) return null

  const diffDays = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    return { text: 'Overdue', classes: 'govuk-tag--red' }
  } else if (diffDays <= 5) {
    return { text: diffDays + ' days left', classes: 'govuk-tag--yellow' }
  }
  return null
}

// Helper: parse "6 September 2024" format dates
function parseGovDate (str) {
  if (!str) return null
  const d = new Date(str)
  return isNaN(d.getTime()) ? null : d
}

// Helper: get workflow for a case
function getWorkflow (workflowPosition, reviewGrounds) {
  const workflowId = reviewGrounds && reviewGrounds.toLowerCase().includes('review')
    ? 'scheduled-review'
    : 'mandatory-reconsideration'

  const workflow = workflows.workflows.find(w => w.id === workflowId) || workflows.workflows[0]
  return workflow
}

// Helper: get matched policy for a case
function getMatchedPolicy (benefitType) {
  return policies.policies.find(p => benefitType.includes(p.benefitType) || p.benefitType.includes(benefitType))
    || policies.policies.find(p => benefitType.toLowerCase().includes(p.benefitType.toLowerCase().split(' ')[0]))
    || null
}

// Helper: get matched decision template for a case
function getDecisionTemplate (benefitType) {
  return decisionTemplates.templates.find(t => benefitType.includes(t.benefitType) || t.benefitType.includes(benefitType))
    || decisionTemplates.templates.find(t => benefitType.toLowerCase().includes(t.benefitType.toLowerCase().split(' ')[0]))
    || null
}

// Helper: count evidence status for a case
function evidenceStatus (caseData) {
  const total = caseData.evidenceRequests.length
  const received = caseData.evidenceRequests.filter(e => e.status === 'Received').length
  const overdue = caseData.evidenceRequests.filter(e => e.status === 'Overdue').length
  const pending = caseData.evidenceRequests.filter(e => e.status === 'Pending').length
  return { total, received, overdue, pending }
}

// Helper: find similar precedent cases for a given case
function getSimilarPrecedents (caseData) {
  // Build a set of tags from the case to match against
  const caseTags = []

  // Benefit type tags
  const bt = caseData.benefitType.toLowerCase()
  if (bt.includes('personal independence')) caseTags.push('pip')
  if (bt.includes('employment and support')) caseTags.push('esa')
  if (bt.includes('universal credit')) caseTags.push('uc')
  if (bt.includes('attendance allowance')) caseTags.push('aa')

  // Criterion tags from review grounds
  const rg = caseData.reviewGrounds.toLowerCase()
  if (rg.includes('mobility')) caseTags.push('mobility')
  if (rg.includes('daily living')) caseTags.push('daily-living')
  if (rg.includes('night')) caseTags.push('night-time')
  if (rg.includes('fit for work') || rg.includes('work capability')) {
    caseTags.push('lcw')
  }
  if (rg.includes('change of circumstances')) caseTags.push('change-of-circumstances')
  if (rg.includes('mandatory reconsideration')) caseTags.push('mandatory-reconsideration')
  if (rg.includes('review')) caseTags.push('award-review')

  // Score each precedent by how many tags match
  const scored = precedents.precedents.map(function (prec) {
    const matchCount = prec.tags.filter(t => caseTags.includes(t)).length
    return { precedent: prec, score: matchCount }
  })

  // Filter to those with at least 2 matching tags, sort by score descending
  return scored
    .filter(s => s.score >= 2)
    .sort((a, b) => b.score - a.score)
    .map(s => s.precedent)
}

// Helper: get quality checklist for a benefit type
function getQualityChecklist (benefitType) {
  return qualityChecklists.checklists.find(c => benefitType.includes(c.benefitType) || c.benefitType.includes(benefitType))
    || qualityChecklists.checklists.find(c => benefitType.toLowerCase().includes(c.benefitType.toLowerCase().split(' ')[0]))
    || null
}

// Helper: replace template placeholders with case data
function populateLetter (bodyTemplate, caseData, caseworker, formData) {
  let text = bodyTemplate

  // Case data replacements
  text = text.replace(/\{\{applicantName\}\}/g, caseData.applicant.name)
  text = text.replace(/\{\{benefitType\}\}/g, caseData.benefitType)
  text = text.replace(/\{\{caseId\}\}/g, caseData.id)
  text = text.replace(/\{\{originalDecisionDate\}\}/g, caseData.originalDecision.date)
  text = text.replace(/\{\{caseworkerName\}\}/g, caseworker ? caseworker.name : 'Caseworker')
  text = text.replace(/\{\{decisionDate\}\}/g, formatTodayDate())

  // Representative replacements
  if (caseData.applicant.representative) {
    text = text.replace(/\{\{representativeName\}\}/g, caseData.applicant.representative.name)
    text = text.replace(/\{\{representativeReference\}\}/g, caseData.applicant.representative.reference)
  }

  // Form field replacements
  if (formData) {
    Object.keys(formData).forEach(function (key) {
      const placeholder = '{{' + key + '}}'
      text = text.replace(new RegExp(placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), formData[key] || '')
    })
  }

  return text
}

// Helper: format today's date in GOV.UK style
function formatTodayDate () {
  const months = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December']
  const d = new Date()
  return d.getDate() + ' ' + months[d.getMonth()] + ' ' + d.getFullYear()
}

// Make helpers available to all templates
router.use(function (req, res, next) {
  res.locals.cases = cases
  res.locals.policies = policies
  res.locals.workflows = workflows
  res.locals.aiNotes = aiNotes
  res.locals.statusTagClass = statusTagClass
  res.locals.deadlineTag = deadlineTag
  res.locals.getWorkflow = getWorkflow
  res.locals.getMatchedPolicy = getMatchedPolicy
  res.locals.evidenceStatus = evidenceStatus
  next()
})

// ============================================================
// V1 Routes
// ============================================================

// Dashboard — caseworker view
router.get('/v1/dashboard', function (req, res) {
  const caseworkerId = req.query.caseworker || 'caseworker-1'
  const caseworker = cases.caseworkers.find(c => c.id === caseworkerId)
  const myCases = cases.cases.filter(c => c.assignedTo === caseworkerId)

  // Sort by deadline (nearest first)
  myCases.sort(function (a, b) {
    const dateA = parseGovDate(a.deadline)
    const dateB = parseGovDate(b.deadline)
    if (!dateA) return 1
    if (!dateB) return -1
    return dateA - dateB
  })

  // Counts
  const atRisk = myCases.filter(function (c) {
    const tag = deadlineTag(c.deadline)
    return tag && tag.classes === 'govuk-tag--yellow'
  }).length

  const overdue = myCases.filter(function (c) {
    const tag = deadlineTag(c.deadline)
    return tag && tag.classes === 'govuk-tag--red'
  }).length

  const needsAction = myCases.filter(function (c) {
    return c.status === 'New' || c.status === 'Ready for decision'
  }).length

  res.render('v1/dashboard', {
    caseworker: caseworker,
    caseworkerId: caseworkerId,
    myCases: myCases,
    aiNotes: aiNotes,
    counts: {
      total: myCases.length,
      atRisk: atRisk,
      overdue: overdue,
      needsAction: needsAction
    }
  })
})

// Case detail view
router.get('/v1/case/:caseId', function (req, res) {
  const caseIndex = cases.cases.findIndex(c => c.id === req.params.caseId)
  const caseData = cases.cases[caseIndex]

  if (!caseData) {
    res.status(404).render('v1/case-not-found')
    return
  }

  // Merge AI-generated summary from ai_notes.json if available for this case
  const aiNote = aiNotes[caseIndex]
  if (aiNote && aiNote.ai_summary) {
    caseData.aiAdvisor = caseData.aiAdvisor || {}
    caseData.aiAdvisor.summary = aiNote.ai_summary
    caseData.aiAdvisor.riskLevel = aiNote.ai_risk_level
    if (aiNote.ai_next_action) {
      const nextAction = typeof aiNote.ai_next_action === 'string'
        ? aiNote.ai_next_action
        : Object.entries(aiNote.ai_next_action).map(([k, v]) => k.replace(/_/g, ' ')).join(', ')
      caseData.aiAdvisor.recommendedActions = [nextAction]
    }
  }

  const caseworker = cases.caseworkers.find(c => c.id === caseData.assignedTo)
  const policy = getMatchedPolicy(caseData.benefitType)
  const workflow = getWorkflow(caseData.workflowPosition, caseData.reviewGrounds)
  const evStatus = evidenceStatus(caseData)

  // Mark workflow steps as completed, current, or future
  const currentStepIndex = workflow.steps.findIndex(s => s.id === caseData.workflowPosition)
  const workflowSteps = workflow.steps.map(function (step, index) {
    let stepStatus = 'future'
    if (index < currentStepIndex) {
      stepStatus = 'completed'
    } else if (index === currentStepIndex) {
      stepStatus = 'current'
    }
    return Object.assign({}, step, { stepStatus: stepStatus })
  })

  // Handle escalated state
  const isEscalated = caseData.workflowPosition === 'escalated'

  // Check if decision template exists for action buttons
  const hasDecisionTemplate = !!getDecisionTemplate(caseData.benefitType)

  // Find similar precedent cases
  const similarPrecedents = getSimilarPrecedents(caseData)

  res.render('v1/case', {
    caseData: caseData,
    caseworker: caseworker,
    policy: policy,
    workflow: workflow,
    workflowSteps: workflowSteps,
    isEscalated: isEscalated,
    evStatus: evStatus,
    hasDecisionTemplate: hasDecisionTemplate,
    similarPrecedents: similarPrecedents
  })
})

// Team leader overview
router.get('/v1/team', function (req, res) {
  const allCases = cases.cases
  const allCaseworkers = cases.caseworkers

  // Summary stats
  const totalOpen = allCases.filter(c => c.status !== 'Decision made' && c.status !== 'Closed').length
  const totalOverdue = allCases.filter(function (c) {
    const tag = deadlineTag(c.deadline)
    return tag && tag.classes === 'govuk-tag--red'
  }).length
  const totalAtRisk = allCases.filter(function (c) {
    const tag = deadlineTag(c.deadline)
    return tag && tag.classes === 'govuk-tag--yellow'
  }).length

  // Workload per caseworker
  const workload = allCaseworkers.map(function (cw) {
    const cwCases = allCases.filter(c => c.assignedTo === cw.id)
    const cwOverdue = cwCases.filter(function (c) {
      const tag = deadlineTag(c.deadline)
      return tag && tag.classes === 'govuk-tag--red'
    }).length
    return {
      caseworker: cw,
      totalCases: cwCases.length,
      overdue: cwOverdue
    }
  })

  res.render('v1/team', {
    allCases: allCases,
    allCaseworkers: allCaseworkers,
    workload: workload,
    counts: {
      totalOpen: totalOpen,
      totalOverdue: totalOverdue,
      totalAtRisk: totalAtRisk,
      totalCases: allCases.length
    }
  })
})

// ============================================================
// Precedent / similar cases routes
// ============================================================

// Similar cases for a given case
router.get('/v1/case/:caseId/similar', function (req, res) {
  const caseData = cases.cases.find(c => c.id === req.params.caseId)

  if (!caseData) {
    res.status(404).render('v1/case-not-found')
    return
  }

  const similarPrecedents = getSimilarPrecedents(caseData)

  res.render('v1/similar-cases', {
    caseData: caseData,
    similarPrecedents: similarPrecedents
  })
})

// Individual precedent detail
router.get('/v1/precedent/:precedentId', function (req, res) {
  const prec = precedents.precedents.find(p => p.id === req.params.precedentId)

  if (!prec) {
    res.status(404).render('v1/case-not-found')
    return
  }

  const fromCase = req.query.from || null

  res.render('v1/precedent', {
    precedent: prec,
    fromCase: fromCase
  })
})

// ============================================================
// Decision routes
// ============================================================

// Record decision — form
router.get('/v1/decision/:caseId', function (req, res) {
  const caseData = cases.cases.find(c => c.id === req.params.caseId)

  if (!caseData) {
    res.status(404).render('v1/case-not-found')
    return
  }

  const template = getDecisionTemplate(caseData.benefitType)

  // Find similar precedent cases for reference while making a decision
  const similarPrecedents = getSimilarPrecedents(caseData)

  res.render('v1/decision', {
    caseData: caseData,
    template: template,
    similarPrecedents: similarPrecedents
  })
})

// Record decision — quality review (new step between form and preview)
router.post('/v1/decision/:caseId', function (req, res) {
  const caseData = cases.cases.find(c => c.id === req.params.caseId)

  if (!caseData) {
    res.status(404).render('v1/case-not-found')
    return
  }

  const checklist = getQualityChecklist(caseData.benefitType)

  res.render('v1/quality-review', {
    caseData: caseData,
    checklist: checklist
  })
})

// Quality review — submit to preview
router.post('/v1/decision/:caseId/preview', function (req, res) {
  const caseData = cases.cases.find(c => c.id === req.params.caseId)

  if (!caseData) {
    res.status(404).render('v1/case-not-found')
    return
  }

  const template = getDecisionTemplate(caseData.benefitType)
  const caseworker = cases.caseworkers.find(c => c.id === caseData.assignedTo)

  // Build decision notice text from template and form data
  const notice = template.noticeTemplate
  let noticeText = notice.opening + '\n\n'

  // Determine outcome from form data
  const outcomeSectionId = template.sections.find(s => s.type === 'decision').id
  const outcomeFieldId = outcomeSectionId + '-outcome'
  const outcomeValue = req.session.data[outcomeFieldId] || 'Decision not recorded'

  if (outcomeValue.toLowerCase().includes('uphold')) {
    noticeText += notice.outcomeUphold + '\n\n'
  } else {
    noticeText += notice.outcomeRevise + '\n\n'
  }

  noticeText += notice.reasoningIntro + '\n\n'

  // Add reasoning from each criterion section
  template.sections.forEach(function (section) {
    if (section.type === 'criterion') {
      section.fields.forEach(function (field) {
        const fieldKey = section.id + '-' + field.id
        const value = req.session.data[fieldKey]
        if (value && field.type === 'textarea') {
          noticeText += value + '\n\n'
        }
      })
    }
  })

  noticeText += notice.appealRights + '\n\n'
  noticeText += notice.closing

  // Replace placeholders
  noticeText = noticeText.replace(/\{\{applicantName\}\}/g, caseData.applicant.name)
  noticeText = noticeText.replace(/\{\{originalDecisionDate\}\}/g, caseData.originalDecision.date)
  noticeText = noticeText.replace(/\{\{caseworkerName\}\}/g, caseworker ? caseworker.name : 'Caseworker')

  res.render('v1/decision-preview', {
    caseData: caseData,
    template: template,
    noticeText: noticeText
  })
})

// Confirm decision
router.post('/v1/decision/:caseId/confirm', function (req, res) {
  const caseData = cases.cases.find(c => c.id === req.params.caseId)

  if (!caseData) {
    res.status(404).render('v1/case-not-found')
    return
  }

  const confirmDecision = req.session.data['confirm-decision']

  if (confirmDecision === 'no') {
    res.redirect('/v1/decision/' + caseData.id)
    return
  }

  res.render('v1/decision-confirmed', {
    caseData: caseData
  })
})

// ============================================================
// Correspondence routes
// ============================================================

// Correspondence — template list
router.get('/v1/correspondence/:caseId', function (req, res) {
  const caseData = cases.cases.find(c => c.id === req.params.caseId)

  if (!caseData) {
    res.status(404).render('v1/case-not-found')
    return
  }

  res.render('v1/correspondence', {
    caseData: caseData,
    templates: correspondenceTemplates.templates
  })
})

// Correspondence — compose
router.get('/v1/correspondence/:caseId/:templateId', function (req, res) {
  const caseData = cases.cases.find(c => c.id === req.params.caseId)
  const template = correspondenceTemplates.templates.find(t => t.id === req.params.templateId)

  if (!caseData || !template) {
    res.status(404).render('v1/case-not-found')
    return
  }

  const caseworker = cases.caseworkers.find(c => c.id === caseData.assignedTo)

  // Pre-fill known values
  const prefills = {}
  if (template.id === 'letter-evidence-chase') {
    // Pre-fill with overdue evidence request details
    const overdueRequest = caseData.evidenceRequests.find(e => e.status === 'Overdue')
    if (overdueRequest) {
      prefills['evidence-type'] = overdueRequest.type
      prefills['original-request-date'] = overdueRequest.requestedDate
    }
  }

  res.render('v1/correspondence-compose', {
    caseData: caseData,
    template: template,
    caseworker: caseworker,
    prefills: prefills
  })
})

// Correspondence — preview
router.post('/v1/correspondence/:caseId/:templateId', function (req, res) {
  const caseData = cases.cases.find(c => c.id === req.params.caseId)
  const template = correspondenceTemplates.templates.find(t => t.id === req.params.templateId)

  if (!caseData || !template) {
    res.status(404).render('v1/case-not-found')
    return
  }

  const caseworker = cases.caseworkers.find(c => c.id === caseData.assignedTo)
  const letterText = populateLetter(template.body, caseData, caseworker, req.session.data)

  res.render('v1/correspondence-preview', {
    caseData: caseData,
    template: template,
    letterText: letterText
  })
})

// Correspondence — send
router.post('/v1/correspondence/:caseId/:templateId/send', function (req, res) {
  const caseData = cases.cases.find(c => c.id === req.params.caseId)
  const template = correspondenceTemplates.templates.find(t => t.id === req.params.templateId)

  if (!caseData || !template) {
    res.status(404).render('v1/case-not-found')
    return
  }

  const confirmSend = req.session.data['confirm-send']

  if (confirmSend === 'no') {
    res.redirect('/v1/correspondence/' + caseData.id + '/' + template.id)
    return
  }

  res.render('v1/correspondence-sent', {
    caseData: caseData,
    template: template
  })
})
