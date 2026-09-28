import { useState } from "react";
import { compareOptions } from "../services/decisionApi";

function ListEditor({
  items,
  setItems,
  placeholder,
  showWeights = false,
  weights = [],
  setWeights,
}) {
  const update = (i, value) => {
    const next = [...items];
    next[i] = value;
    setItems(next);
  };

  const canRemove = items.length > (placeholder === "Criterion" ? 1 : 2);

  const addItem = () => {
    setItems([...items, ""]);

    if (showWeights && setWeights) {
      setWeights([...weights, 3]);
    }
  };

  const removeItem = (i) => {
    setItems(items.filter((_, idx) => idx !== i));

    if (showWeights && setWeights) {
      setWeights(weights.filter((_, idx) => idx !== i));
    }
  };

  return (
    <div className="decision-list-editor">
      {items.map((item, i) => (
        <div className="decision-input-row decision-input-row-expanded" key={i}>
          <div className="decision-input-number">
            {String(i + 1).padStart(2, "0")}
          </div>

          <input
            value={item}
            onChange={(e) => update(i, e.target.value)}
            placeholder={`${placeholder} ${i + 1}`}
          />

          {showWeights && (
            <div className="decision-weight-control">
              <span>Importance</span>

              <select
                value={weights[i] ?? 3}
                onChange={(e) => {
                  const next = [...weights];
                  next[i] = Number(e.target.value);
                  setWeights(next);
                }}
              >
                <option value={1}>1 — Low</option>
                <option value={2}>2 — Moderate</option>
                <option value={3}>3 — Important</option>
                <option value={4}>4 — Very important</option>
                <option value={5}>5 — Critical</option>
              </select>
            </div>
          )}

          {canRemove && (
            <button
              type="button"
              className="decision-remove"
              onClick={() => removeItem(i)}
              title={`Remove ${placeholder.toLowerCase()}`}
            >
              ×
            </button>
          )}
        </div>
      ))}

      <button
        type="button"
        className="decision-add"
        onClick={addItem}
      >
        <span>+</span>
        Add {placeholder}
      </button>
    </div>
  );
}

function DecisionSupportPanel() {
  const [options, setOptions] = useState(["", ""]);
  const [criteria, setCriteria] = useState([""]);
  const [weights, setWeights] = useState([3]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const runComparison = async () => {
    const cleanOptions = options.map((o) => o.trim()).filter(Boolean);

    const cleanCriteriaData = criteria
      .map((criterion, index) => ({
        criterion: criterion.trim(),
        weight: Number(weights[index] ?? 3),
      }))
      .filter((item) => item.criterion);

    const cleanCriteria = cleanCriteriaData.map((item) => item.criterion);

    const cleanWeights = {};

    cleanCriteriaData.forEach((item) => {
      cleanWeights[item.criterion] = item.weight;
    });

    if (cleanOptions.length < 2 || cleanCriteria.length < 1) {
      alert("Enter at least 2 options and 1 criterion.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const res = await compareOptions(
        cleanOptions,
        cleanCriteria,
        cleanWeights
      );

      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Comparison failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="decision-page">
      <div className="decision-hero">
        <div>
          <div className="decision-eyebrow">
            <span className="decision-live-dot"></span>
            AI TWIN DECISION ENGINE
          </div>

          <h1>Decision Support</h1>

          <p>
            Compare your options against criteria you choose. Your AI Twin
            structures the comparison while you define what matters.
          </p>
        </div>

        <div className="decision-core-mini">
          <span>AI</span>
        </div>
      </div>

      <div className="decision-workspace">
        <section className="decision-setup-panel">
          <div className="decision-panel-header">
            <div>
              <span className="decision-panel-kicker">STEP 01</span>
              <h2>Define your comparison</h2>
            </div>

            <div className="decision-panel-badge">CUSTOM</div>
          </div>

          <p className="decision-panel-description">
            Add at least two options and one criterion. Set how important
            each criterion is so the final score reflects your priorities.
          </p>

          <div className="decision-section">
            <div className="decision-section-heading">
              <div>
                <span className="decision-section-kicker">OPTIONS</span>
                <h3>What are you comparing?</h3>
              </div>

              <span className="decision-section-count">
                {options.filter((o) => o.trim()).length}
              </span>
            </div>

            <ListEditor
              items={options}
              setItems={setOptions}
              placeholder="Option"
            />
          </div>

          <div className="decision-divider"></div>

          <div className="decision-section">
            <div className="decision-section-heading">
              <div>
                <span className="decision-section-kicker">CRITERIA</span>
                <h3>What matters to you?</h3>
              </div>

              <span className="decision-section-count">
                {criteria.filter((c) => c.trim()).length}
              </span>
            </div>

            <ListEditor
              items={criteria}
              setItems={setCriteria}
              placeholder="Criterion"
              showWeights
              weights={weights}
              setWeights={setWeights}
            />

            <div className="decision-weight-help">
              <span>WEIGHTING</span>
              <p>
                Higher importance means that criterion contributes more to
                the final weighted total.
              </p>
            </div>
          </div>

          <button
            type="button"
            className="decision-compare-button"
            onClick={runComparison}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="decision-button-spinner"></span>
                Comparing...
              </>
            ) : (
              <>
                Run Comparison
                <span>→</span>
              </>
            )}
          </button>

          <div className="decision-note">
            <span>i</span>
            You define both the criteria and their importance. The AI Twin
            does not assume your preferences.
          </div>
        </section>

        <section className="decision-results-panel">
          <div className="decision-panel-header">
            <div>
              <span className="decision-panel-kicker">STEP 02</span>
              <h2>Comparison results</h2>
            </div>

            {result?.options?.length > 0 && (
              <div className="decision-panel-badge">
                {result.options.length} options
              </div>
            )}
          </div>

          {!result && !loading && (
            <div className="decision-empty">
              <div className="decision-empty-core">
                <span>AI</span>
              </div>

              <h3>Ready when you are</h3>

              <p>
                Add your options and criteria on the left, set their
                importance, then run the comparison to see scores,
                trade-offs and assumptions.
              </p>
            </div>
          )}

          {loading && (
            <div className="decision-loading">
              <div className="decision-loading-core"></div>
              <h3>Analyzing options...</h3>
              <p>
                Your AI Twin is comparing the options against your weighted
                criteria.
              </p>
            </div>
          )}

          {result && result.error && (
            <div className="decision-error">
              <strong>Comparison could not be completed</strong>
              <span>{result.error}</span>
            </div>
          )}

          {result && result.options && result.options.length > 0 && (
            <div className="decision-result-content">
              <div className="decision-table-wrapper">
                <table className="decision-table">
                  <thead>
                    <tr>
                      <th>OPTION</th>

                      {Object.keys(result.options[0].scores || {}).map(
                        (criterion) => (
                          <th key={criterion}>
                            {criterion}
                            <span className="decision-weight-header">
                              × {cleanWeightLabel(cleanWeightValue(criterion, criteria, weights))}
                            </span>
                          </th>
                        )
                      )}

                      <th>WEIGHTED TOTAL</th>
                    </tr>
                  </thead>

                  <tbody>
                    {result.options.map((opt, i) => (
                      <tr key={i}>
                        <td>
                          <span className="decision-option-name">
                            {opt.name}
                          </span>
                        </td>

                        {Object.entries(opt.scores || {}).map(
                          ([criterion, score]) => (
                            <td
                              key={criterion}
                              title={score.justification}
                            >
                              <span className="decision-score">
                                {score.score}
                                <small>/10</small>
                              </span>
                            </td>
                          )
                        )}

                        <td>
                          <span className="decision-total">
                            {opt.weighted_total}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {result.recommendation && (
                <div className="decision-recommendation">
                  <div className="decision-result-icon">RESULT</div>

                  <div>
                    <span className="decision-result-kicker">
                      AI ANALYSIS
                    </span>
                    <h3>Comparison Summary</h3>
                    <p>{result.recommendation}</p>
                  </div>
                </div>
              )}

              {result.trade_offs && result.trade_offs.length > 0 && (
                <div className="decision-detail-card">
                  <div className="decision-detail-header">
                    <span className="decision-detail-icon">TRADE</span>

                    <div>
                      <span className="decision-result-kicker">
                        BALANCE
                      </span>
                      <h3>Trade-offs</h3>
                    </div>
                  </div>

                  <ul>
                    {result.trade_offs.map((tradeOff, i) => (
                      <li key={i}>{tradeOff}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.assumptions && result.assumptions.length > 0 && (
                <div className="decision-detail-card decision-assumptions">
                  <div className="decision-detail-header">
                    <span className="decision-detail-icon">ASSUME</span>

                    <div>
                      <span className="decision-result-kicker">
                        CONTEXT
                      </span>
                      <h3>Assumptions made</h3>
                    </div>
                  </div>

                  <ul>
                    {result.assumptions.map((assumption, i) => (
                      <li key={i}>{assumption}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function cleanWeightValue(criterion, criteria, weights) {
  const index = criteria.indexOf(criterion);
  return index >= 0 ? Number(weights[index] ?? 3) : 3;
}

function cleanWeightLabel(value) {
  return value;
}

export default DecisionSupportPanel;
