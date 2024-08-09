from paper_eta.src.libs.renderer.waveshare.epd3in7.mixed import row_6_eta_3
from paper_eta.src.libs import renderer
from paper_eta.src.libs.hketa.test import TESTS_TC

row_6_eta_3.Renderer().draw(TESTS_TC)["black"].save("./test.png")
