  const portfolioLink = document.getElementById("portfolioLink");
  const portfolioFile = document.getElementById("portfolioFile");
  const portfolioLinkBlock = document.getElementById("portfolioLinkBlock");
  const portfolioFileBlock = document.getElementById("portfolioFileBlock");

  const togglePortfolioBlocks = () => {
    const isLink = portfolioLink.checked;
    portfolioLinkBlock.classList.toggle("d-none", !isLink);
    portfolioFileBlock.classList.toggle("d-none", isLink);
  };

  portfolioLink.addEventListener("change", togglePortfolioBlocks);
  portfolioFile.addEventListener("change", togglePortfolioBlocks);
