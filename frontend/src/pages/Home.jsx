import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { signOut } from 'firebase/auth';
import { auth } from '../services/firebase';
import './Welcome.css';

export default function Home() {
  const { user, loading } = useAuth();

  return (
    <div className="welcome-root">
      <header className="top">
        <Link className="brand" to="/">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
            <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
          </svg>
          FieldMind
        </Link>
        <div className="auth">
          {!loading && (
            !user ? (
              <>
                <Link className="a-btn a-login" to="/login">Login</Link>
                <Link className="a-btn a-reg" to="/register">Register</Link>
              </>
            ) : (
              <>
                <Link className="a-btn a-reg" to="/dashboard">Dashboard</Link>
                <button
                  type="button"
                  className="a-btn a-login"
                  onClick={() => signOut(auth)}
                >
                  Logout
                </button>
              </>
            )
          )}
        </div>
      </header>

      <div className="blob b1"></div>
      <div className="blob b2"></div>
      <div className="dots"></div>

      <div className="main">
        <section className="left">
          <span className="tag"><i></i> AI-Powered Crop Intelligence</span>
          <h1>Healthier crops,<br />from a <em>single leaf.</em></h1>
          <p className="sub">
            Upload a leaf photo and get an AI diagnosis in moments, then find the best crops for your soil and climate. Built for farmers.
          </p>
          <div className="cta">
            <Link className="btn btn-p" to="/disease-detection">
              Detect Disease
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M13 6l6 6-6 6"/>
              </svg>
            </Link>
            <Link className="btn btn-o" to="/crop-recommendation">
              Recommend Crop
            </Link>
          </div>
          <div className="also">
            Also inside:
            <Link to="/diagnosis-history" className="c">Diagnosis History</Link>
            <Link to="/equipment" className="c">Equipment Rental</Link>
            <Link to="/workforce" className="c">Farm Workforce</Link>
          </div>
        </section>

        <section className="right">
          <div className="stage">
            <div className="disc"></div>
            <div className="ring2"></div>

            <div className="card verify">
              <span className="ck">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 6L9 17l-5-5"/>
                </svg>
              </span>
              Valid plant leaf
            </div>

            <div className="leafbox">
              <svg viewBox="0 0 400 440">
                <defs>
                  <linearGradient id="lg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0" stopColor="#76bb5f"/>
                    <stop offset="1" stopColor="#3b7a33"/>
                  </linearGradient>
                </defs>
                <path d="M200,425 L200,438" stroke="#2f6a2d" strokeWidth="7" strokeLinecap="round"/>
                <path d="M200,20 C330,70 380,210 300,340 C270,385 230,410 200,425 C170,410 130,385 100,340 C20,210 70,70 200,20 Z" fill="url(#lg)" stroke="#2f6a2d" strokeWidth="2.5"/>
                <path d="M200,20 C70,70 20,210 100,340 C130,385 170,410 200,425 Z" fill="rgba(0,0,0,.09)"/>
                <g fill="none" stroke="rgba(214,238,200,.85)" strokeLinecap="round">
                  <path d="M200,30 C196,150 204,300 200,428" strokeWidth="4.5"/>
                  <g strokeWidth="2.6">
                    <path d="M199,90 C170,100 140,115 112,140"/>
                    <path d="M199,150 C165,160 130,180 92,215"/>
                    <path d="M199,215 C165,225 130,245 100,285"/>
                    <path d="M199,280 C175,290 150,305 128,330"/>
                    <path d="M201,90 C230,100 260,115 288,140"/>
                    <path d="M201,150 C235,160 270,180 308,215"/>
                    <path d="M201,215 C235,225 270,245 300,285"/>
                    <path d="M201,280 C225,290 250,305 272,330"/>
                  </g>
                </g>
                {/* lesions */}
                <circle className="halo" cx="150" cy="175" r="24" fill="rgba(222,190,70,.55)"/>
                <circle cx="150" cy="175" r="13" fill="#7a4a22"/>
                <circle cx="150" cy="175" r="6" fill="#4d2c12"/>
                <circle className="halo" cx="252" cy="235" r="29" fill="rgba(222,190,70,.55)" style={{ animationDelay: '-1s' }}/>
                <circle cx="252" cy="235" r="17" fill="#7a4a22"/>
                <circle cx="252" cy="235" r="8" fill="#4d2c12"/>
                <circle cx="190" cy="320" r="9" fill="#7a4a22" opacity=".9"/>
                <circle cx="190" cy="320" r="4" fill="#4d2c12"/>
                {/* detection boxes */}
                <g className="bx bx1">
                  <rect x="114" y="139" width="72" height="72" rx="8" fill="rgba(232,163,61,.1)" stroke="#e8a33d" strokeWidth="3"/>
                  <rect x="114" y="117" width="98" height="22" rx="6" fill="#e8a33d"/>
                  <text x="123" y="132.5" fontFamily="Inter, sans-serif" fontSize="12" fontWeight="700" fill="#fff">Early blight</text>
                </g>
                <g className="bx bx2">
                  <rect x="208" y="191" width="88" height="88" rx="8" fill="rgba(232,163,61,.1)" stroke="#e8a33d" strokeWidth="3"/>
                  <rect x="208" y="169" width="98" height="22" rx="6" fill="#e8a33d"/>
                  <text x="217" y="184.5" fontFamily="Inter, sans-serif" fontSize="12" fontWeight="700" fill="#fff">Early blight</text>
                </g>
              </svg>
              <div className="scan"></div>
            </div>

            <div className="card result">
              <div className="k">Diagnosis</div>
              <div className="dz">
                <div className="ic">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11 2v2"/><path d="M5 2v2"/><path d="M5 3H4a2 2 0 0 0-2 2v4a6 6 0 0 0 12 0V5a2 2 0 0 0-2-2h-1"/><path d="M8 15a6 6 0 0 0 12 0v-3"/><circle cx="20" cy="10" r="2"/>
                  </svg>
                </div>
                <div>
                  <b>Early Blight</b>
                  <small>Tomato leaf</small>
                </div>
              </div>
              <div className="meter"><i></i></div>
              <div className="conf">
                <span>Confidence</span>
                <span>94%</span>
              </div>
            </div>

            <div className="card recs">
              <div className="k">Crop recommendation</div>
              <div className="rec">
                <span className="n">Rice</span>
                <div className="t"><i style={{ '--w': '92%' }}></i></div>
                <em>92%</em>
              </div>
              <div className="rec">
                <span className="n">Groundnut</span>
                <div className="t"><i style={{ '--w': '85%' }}></i></div>
                <em>85%</em>
              </div>
              <div className="rec">
                <span className="n">Maize</span>
                <div className="t"><i style={{ '--w': '78%' }}></i></div>
                <em>78%</em>
              </div>
              <div className="env">
                <span>Loamy soil</span>
                <span>28°C</span>
              </div>
            </div>
            <span className="sample">Sample preview</span>
          </div>
        </section>
      </div>

      <div className="steps">
        <Link to="/disease-detection" className="step">
          <div className="no">1</div>
          <div>
            <b>Verify the leaf</b>
            <span>Checks the image is a valid plant leaf</span>
          </div>
        </Link>
        <Link to="/disease-detection" className="step">
          <div className="no">2</div>
          <div>
            <b>Detect the disease</b>
            <span>AI identifies the crop disease</span>
          </div>
        </Link>
        <Link to="/crop-recommendation" className="step">
          <div className="no">3</div>
          <div>
            <b>Recommend a crop</b>
            <span>Best picks for your soil and climate</span>
          </div>
        </Link>
      </div>
    </div>
  );
}
