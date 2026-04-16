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
function getWorkflow (workflowPosition, benefitType) {
  // Determine workflow type from benefit type or default to mandatory reconsideration
  const workflowId = benefitType && benefitType.includes('review')
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

// Helper: count evidence status for a case
function evidenceStatus (caseData) {
  const total = caseData.evidenceRequests.length
  const received = caseData.evidenceRequests.filter(e => e.status === 'Received').length
  const overdue = caseData.evidenceRequests.filter(e => e.status === 'Overdue').length
  const pending = caseData.evidenceRequests.filter(e => e.status === 'Pending').length
  return { total, received, overdue, pending }
}

// Make helpers available to all templates
router.use(function (req, res, next) {
  res.locals.cases = cases
  res.locals.policies = policies
  res.locals.workflows = workflows
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
  const caseData = cases.cases.find(c => c.id === req.params.caseId)

  if (!caseData) {
    res.status(404).render('v1/case-not-found')
    return
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

  res.render('v1/case', {
    caseData: caseData,
    caseworker: caseworker,
    policy: policy,
    workflow: workflow,
    workflowSteps: workflowSteps,
    isEscalated: isEscalated,
    evStatus: evStatus
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
