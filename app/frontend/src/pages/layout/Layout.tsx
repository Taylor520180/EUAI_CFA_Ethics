import { Outlet, NavLink, Link } from "react-router-dom";

import github from "../../assets/logo.png";

import styles from "./Layout.module.css";

import { useLogin } from "../../authConfig";

import { LoginButton } from "../../components/LoginButton";

const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <a href="#" target={"_blank"} title="EAIB">
                        <img src={github} alt="EAIBEU logo" aria-label="Link to github repository" width="121px" height="45px" className={styles.githubLogo} />
                    </a>
                    <nav>
                        <ul className={styles.headerNavList}>
                            <li>
                                <NavLink to="/" className={({ isActive }) => (isActive ? styles.headerNavPageLinkActive : styles.headerNavPageLink)}></NavLink>
                            </li>
                            <li className={styles.headerNavLeftMargin}></li>
                        </ul>
                    </nav>
                    <h4 className={styles.headerRightText}>Enhanced Study with AI</h4>
                    {useLogin && <LoginButton />}
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
