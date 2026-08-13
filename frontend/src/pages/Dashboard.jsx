import { useState, useEffect, useRef } from 'react'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import s from './Dashboard.module.css'
import AlertBanner from '../components/AlertBanner'
import MetricCard from '../components/MetricCard'
import BudgetCard from '../components/BudgetCard'
import FormTable from '../components/FormTable'
import BudgetChart from '../components/BudgetChart'
import DetailModal from '../components/DetailModal'
import AllMonthlyDetailModal from '../components/AllMonthlyDetailModal'
import PrStatusModal from '../components/PrStatusModal'
import PrTrackingModal from '../components/PrTrackingModal'
import MonthlyPipelineChart from '../components/MonthlyPipelineChart'
import CancelledPlanningModal from '../components/CancelledPlanningModal'
import { budgetApi } from '../api/budgetApi'
import { prApi } from '../api/prApi'
import { formatRp } from '../utils/format'

const CURRENT_YEAR = String(new Date().getFullYear())

export default function Dashboard() {
  const [selectedForm, setSelectedForm] = useState(null)
  const [summary, setSummary] = useState(null)
  const [prSummary, setPrSummary] = useState(null)
  const [monthlySummary, setMonthlySummary] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isExporting, setIsExporting] = useState(false)
  const dashboardRef = useRef(null)
  const [showCancelledPlanningModal, setShowCancelledPlanningModal] = useState(false)

  const handleExportAll = async () => {
    if (!dashboardRef.current) return
    try {
      setIsExporting(true)
      const canvas = await html2canvas(dashboardRef.current, { scale: 2, useCORS: true, backgroundColor: '#ffffff' })
      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF('p', 'mm', 'a4') // Portrait A4

      const pdfWidth = pdf.internal.pageSize.getWidth()
      const margin = 10
      const contentWidth = pdfWidth - (margin * 2)
      const contentHeight = (canvas.height * contentWidth) / canvas.width

      pdf.addImage(imgData, 'PNG', margin, margin, contentWidth, contentHeight)
      pdf.save(`dashboard_report_${CURRENT_YEAR}.pdf`)
    } catch (error) {
      console.error('Error exporting PDF:', error)
    } finally {
      setIsExporting(false)
    }
  }

  useEffect(() => {
    fetchSummary()
  }, [])

  async function fetchSummary() {
    setLoading(true)
    setError('')
    try {
      const [resBudget, resPr, resMonthly] = await Promise.all([
        budgetApi.getSummary(CURRENT_YEAR),
        prApi.getDashboardSummary(CURRENT_YEAR),
        prApi.getDashboardSummaryMonthly(CURRENT_YEAR)
      ])

      if (resBudget.success) {
        setSummary(resBudget.data)
      } else {
        setError(resBudget.message || 'Gagal memuat data budget')
      }

      if (resPr.data?.success) {
        setPrSummary(resPr.data.data)
      }

      if (resMonthly.data?.success) {
        setMonthlySummary(resMonthly.data.data)
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Gagal memuat data dashboard')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className={s.page}>
        <div className={s.header}>
          <div className={s.headerLeft}>
            <h1>Dashboard</h1>
            <p>Memuat data...</p>
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: 60, color: '#73726c' }}>
          ⏳ Memuat data dashboard...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={s.page}>
        <div className={s.header}>
          <div className={s.headerLeft}>
            <h1>Dashboard</h1>
            <p>Monitoring budget {CURRENT_YEAR}</p>
          </div>
        </div>
        <div style={{ textAlign: 'center', padding: 60, color: '#e85d3a' }}>
          ⚠ {error}
          <br />
          <button className="btn-secondary" style={{ marginTop: 12 }} onClick={fetchSummary}>
            Coba lagi
          </button>
        </div>
      </div>
    )
  }

  // Build data from API response
  const totalBudget = summary?.total_budget ?? 0
  const totalActual = summary?.total_actual ?? 0
  const totalSaldo = summary?.total_saldo ?? 0
  const overCount = summary?.over_count ?? 0

  const capex = summary?.capex ?? { budget: 0, actual: 0, saldo: 0 }
  const opex = summary?.opex ?? { budget: 0, actual: 0, saldo: 0 }
  const items = summary?.items ?? []

  // Build alerts for over-budget items
  const alerts = items
    .filter(i => i.is_over)
    .map(i => ({
      title: `Budget ${i.kode} melebihi batas`,
      desc: `Actual ${formatRp(i.actual)} · Budget ${formatRp(i.budget)} · Over ${Math.abs(Math.round((i.saldo / i.budget) * 100))}%`,
    }))

  // Build budget data for FormTable
  const budgetData = {}
  items.forEach(i => {
    budgetData[i.kode] = {
      budget: i.budget,
      actual: i.actual,
      saldo: i.saldo,
    }
  })

  // Build chart data
  const chartCapexOpex = [
    { name: 'CAPEX', actual: capex.actual, saldo: capex.saldo, budget: capex.budget },
    { name: 'OPEX', actual: opex.actual, saldo: opex.saldo, budget: opex.budget },
  ]

  const chartForm = items.map(i => ({
    name: i.kode,
    actual: i.actual,
    saldo: i.saldo,
    budget: i.budget,
  }))

  // Find over-budget items for warning sub text
  const overItems = items.filter(i => i.is_over).map(i => i.kode)
  const overSubText = overItems.length > 0
    ? `${overItems.join(', ')} perlu perhatian`
    : 'Semua dalam batas'

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 600, letterSpacing: '-0.02em', marginBottom: '0.25rem' }}>Dashboard</h1>
          <p style={{ color: 'var(--text2)', fontSize: '0.9375rem' }}>Monitoring budget & PR Pipeline {CURRENT_YEAR}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontSize: '0.875rem', color: 'var(--text2)', background: 'var(--bg2)', padding: '8px 16px', borderRadius: '8px', border: '0.5px solid var(--border)' }}>
            Jan — Des {CURRENT_YEAR}
          </span>
          <button
            className="btn-primary"
            onClick={handleExportAll}
            disabled={isExporting}
            style={{ padding: '9px 16px', background: 'var(--text)', fontSize: '0.875rem' }}
          >
            {isExporting ? 'Exporting...' : '⬇ Export PDF'}
          </button>
        </div>
      </div>

      {alerts.length > 0 && <AlertBanner alerts={alerts} />}

      <div ref={dashboardRef} style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

        {/* BUDGET OVERVIEW SECTION */}
        <section className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1.25rem', letterSpacing: '-0.01em' }}>Budget Overview</h2>
          <div className={s.metricGrid}>
            <MetricCard
              label="Total budget"
              value={formatRp(totalBudget)}
              sub="CAPEX + OPEX"
            />
            <MetricCard
              label="Terpakai"
              value={formatRp(totalActual)}
              sub={totalBudget > 0 ? `${Math.round((totalActual / totalBudget) * 100)}% dari total` : '—'}
              variant="danger"
            />
            <MetricCard
              label="Saldo"
              value={formatRp(totalSaldo)}
              sub={totalBudget > 0 ? `${Math.round((totalSaldo / totalBudget) * 100)}% dari total` : '—'}
              variant="success"
            />
            <MetricCard
              label="Over budget"
              value={`${overCount} form`}
              sub={overSubText}
              variant={overCount > 0 ? 'warning' : 'default'}
            />
          </div>
        </section>

        {/* PR PIPELINE SECTION */}
        <section className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1.25rem', letterSpacing: '-0.01em' }}>PR Pipeline Status</h2>
          <div className={s.metricGrid}>
            <MetricCard
              label="Planning Active"
              value={prSummary?.planning_active || 0}
              sub="Form Planning"
              variant="info"
            />
            <MetricCard
              label="Total PR"
              value={prSummary?.total_pr || 0}
              sub="Data Uploaded"
              variant="yellow"
            />
            <MetricCard
              label="Total Matched"
              value={prSummary?.total_matched || 0}
              sub="Ke Planning Detail"
              variant="success"
            />
            <MetricCard
              label="Need Mapping"
              value={prSummary?.need_mapping || 0}
              sub="Belum di-mapping"
              variant="purple"
            />

            <MetricCard
              label="ON PLAN"
              value={prSummary?.on_plan || 0}
              sub="Dalam Budget"
              variant="success"
              onClick={() => setSelectedForm('ON_PLAN')}
            />
            <MetricCard
              label="OVER BUDGET"
              value={prSummary?.over_plan || 0}
              sub="Melebihi Budget"
              variant="warning"
              onClick={() => setSelectedForm('OVER_PLAN')}
            />
            <MetricCard
              label="UNDER PLAN"
              value={prSummary?.under_plan || 0}
              sub="Dibawah Budget"
              variant="info"
              onClick={() => setSelectedForm('UNDER_PLAN')}
            />
            <MetricCard
              label="OOP"
              value={prSummary?.oop || 0}
              sub="Out of Plan"
              variant="danger"
              onClick={() => setSelectedForm('OOP')}
            />
            <MetricCard
              label="Remaining Budget"
              value={formatRp(prSummary?.remaining_budget || 0)}
              sub="Total Plan - Used"
              variant={(prSummary?.remaining_budget || 0) < 0 ? 'danger' : 'success'}
            />
            <MetricCard
              label="Dibatalkan"
              value={prSummary?.cancelled_count || 0}
              sub={`${formatRp(prSummary?.cancelled_amount || 0)}`}
              variant="danger"
              onClick={() => setShowCancelledPlanningModal(true)}
            />
          </div>
        </section>

        {/* TRACKING STAGE SECTION */}
        <section className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1.25rem', letterSpacing: '-0.01em' }}>Document Tracking Stage</h2>
          <div className={s.metricGrid}>
            <MetricCard
              label="PR Stage"
              value={prSummary?.pr_stage || 0}
              sub="Purchase Requisition"
              variant="info"
              onClick={() => setSelectedForm('STAGE_PR')}
            />
            <MetricCard
              label="PO Stage"
              value={prSummary?.po_stage || 0}
              sub="Purchase Order"
              variant="warning"
              onClick={() => setSelectedForm('STAGE_PO')}
            />
            <MetricCard
              label="GR Stage"
              value={prSummary?.gr_stage || 0}
              sub="Goods Receipt"
              variant="success"
              onClick={() => setSelectedForm('STAGE_GR')}
            />
          </div>


          {/* Monthly Breakdown Chart */}
          <div style={{ marginTop: '1.5rem' }}>
            <MonthlyPipelineChart title="Statistik PR per Bulan" data={monthlySummary} />
          </div>
        </section>

        {/* CAPEX VS OPEX SECTION */}
        <section className="card" style={{ padding: '1.5rem', background: 'transparent', border: 'none' }}>
          <div className={s.budgetGrid}>
            <BudgetCard type="CAPEX" {...capex} onClick={() => setSelectedForm('CAPEX')} />
            <BudgetCard type="OPEX" {...opex} onClick={() => setSelectedForm('OPEX')} />
          </div>

          <div className={s.chartGrid}>
            <BudgetChart title="Grafik CAPEX vs OPEX" data={chartCapexOpex} />
            <BudgetChart title="Grafik per form" data={chartForm} />
          </div>
        </section>

        {/* FORM TABLE SECTION */}
        <section className="card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1.25rem', letterSpacing: '-0.01em' }}>Rincian Form</h2>
          <FormTable data={budgetData} onRowClick={setSelectedForm} />
        </section>
      </div>

      {selectedForm === 'ALL' ? (
        <AllMonthlyDetailModal
          periode={CURRENT_YEAR}
          onClose={() => setSelectedForm(null)}
        />
      ) : ['ON_PLAN', 'OVER_PLAN', 'UNDER_PLAN', 'OOP'].includes(selectedForm) ? (
        <PrStatusModal
          status={selectedForm}
          onClose={() => setSelectedForm(null)}
        />
      ) : ['STAGE_PR', 'STAGE_PO', 'STAGE_GR'].includes(selectedForm) ? (
        <PrTrackingModal
          stage={selectedForm.replace('STAGE_', '')}
          onClose={() => setSelectedForm(null)}
        />
      ) : selectedForm ? (
        <DetailModal
          type={selectedForm}
          periode={CURRENT_YEAR}
          summaryItems={items}
          onClose={() => {
            setSelectedForm(null)
            fetchSummary()
          }}
        />
      ) : null}
      {showCancelledPlanningModal && (
        <CancelledPlanningModal
          periode={CURRENT_YEAR}
          onClose={() => { setShowCancelledPlanningModal(false); fetchSummary(); }}
        />
      )}
    </div>
  )
}