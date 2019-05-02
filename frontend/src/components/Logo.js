import React from "react";

const Logo = () => (
  <div className="logo">
    <svg xmlns="http://www.w3.org/2000/svg" height="57" width="50">
      <defs>
        <linearGradient
          id="A"
          y2="253.348"
          spreadMethod="reflect"
          gradientUnits="userSpaceOnUse"
          x2="336.226"
          y1="86.665"
          x1="191.88"
        >
          <stop stop-opacity=".996" stop-color="#d81c1c" offset="0" />
          <stop stop-opacity=".996" stop-color="#053d82" offset=".745" />
        </linearGradient>
      </defs>
      <path
        transform="matrix(.34639 0 0 .34198 -66.465368 -29.636993)"
        fill="url(#A)"
        d="M191.9 86.663L336.23 170 191.9 253.34z"
      />
    </svg>
    <p>KEY</p>
  </div>
);

export default Logo;
