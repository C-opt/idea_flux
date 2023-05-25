
// set the dimensions and margins of the graph
const margin = { top: 80, right: 30, bottom: 30, left: 200 },
    width = 600 - margin.left - margin.right,
    height = 1200 - margin.top - margin.bottom;

// append the svg object to the body of the page
const svg = d3.select("#my_dataviz")
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

d3.json("/subreddits/top5-th")
    .then(function (data) {
        const myIds = Array.from(new Set(data.map(d => d.subreddit_display_name)))
        const myUEs = Array.from(new Set(data.map(d => d.user_engagement)))
        const myTops = ["top 1", "top 2", "top 3", "top 4", "top 5"]

        const x = d3.scaleBand()
            .range([0, width])
            .domain(myTops)
            .padding(0.05);
        svg.append("g")
            .style("font-size", 60)
            .attr("transform", `translate(0, 0)`)
            // .attr("transform", `translate(0, ${height})`)
            .call(d3.axisTop(x).tickSize(0))
            .select(".domain").remove()

        // Build Y scales and axis:
        const y = d3.scaleBand()
            .range([0, height])
            .domain(myIds)
            .padding(0.25);
        svg.append("g")
            .style("font-size", 40)
            .call(d3.axisLeft(y).tickSize(0))
            .select(".domain").remove()

        const myColor = d3.scaleSequential()
            .interpolator(d3.interpolatePlasma)
            .domain([0, d3.max(myUEs)])

        // create a tooltip
        const tooltip = d3.select("#my_tooltip")
            .append("div")
            .style("opacity", 0)
            .attr("class", "tooltip")
            .style("background-color", "white")
            .style("border", "solid")
            .style("border-width", "2px")
            .style("border-radius", "15px")
            .style("padding", "10px")
            .style("width", width + "px")


        // Three function that change the tooltip when user hover / move / leave a cell
        var global_clicked_flag = false
        var clicked_obj = null
        const mouseover = function (event, d) {
            if (global_clicked_flag == false) {
                tooltip
                    .style("opacity", 1)
                d3.select(this)
                    .style("stroke", "black")
                    .style("opacity", 1)
            }
        }
        const mousemove = function (event, d) {
            if (global_clicked_flag == false) {
                tooltip
                    .html(

                        // <a href="url">link text</a>

                        "<h3>" + d.title + " <a href='" + d.url + "'> (link)</a> </h3>" +
                        "<p>" + d.spine_body + "</p>" +
                        "<h4> User engagement: " + d.user_engagement + "</h4>" +
                        "<h4> Subreddit: " + d.subreddit_display_name + "</h4>"
                    )
                // .style("left", (event.x) + "px")
                // .style("top", (event.y) + "px")
            }
        }
        const mouseleave = function (event, d) {
            if (global_clicked_flag == false) {
                tooltip
                    .style("opacity", 0)
                d3.select(this)
                    .style("stroke", "none")
                    .style("opacity", 0.8)
            }
        }

        const mouseclick = function (event, d) {
            if (global_clicked_flag == false) {
                tooltip
                    .style("opacity", 1)
                d3.select(this)
                    .style("stroke", "black")
                    .style("opacity", 1)
                global_clicked_flag = true
                clicked_obj = this

            } else if (this == clicked_obj) {
                tooltip
                    .style("opacity", 0)
                d3.select(this)
                    .style("stroke", "none")
                    .style("opacity", 0.8)
                global_clicked_flag = false
                clicked_obj = this

            } else if (this != clicked_obj) {
                d3.select(clicked_obj)
                    .style("stroke", "none")
                    .style("opacity", 0.8)
                global_clicked_flag = false
            }
        }

        // add the squares
        svg.selectAll()
            .data(data, function (d) {
                d.clicked_flag = false
                return d.subreddit_display_name + ':' + d.user_engagement;
            })
            .join("rect")
            .attr("x", function (d, i) {
                return x(myTops[(d.ua_rank - 1) % 5])
            })
            .attr("y", function (d) { return y(d.subreddit_display_name) })
            .attr("rx", 6)
            .attr("ry", 6)
            .attr("width", x.bandwidth())
            .attr("height", y.bandwidth())
            .style("fill", function (d) { return myColor(d.user_engagement) })
            .style("stroke-width", 4)
            .style("stroke", "none")
            .style("opacity", 0.8)
            .on("mouseover", mouseover)
            .on("mousemove", mousemove)
            .on("mouseleave", mouseleave)
            .on("click", mouseclick)

        console.log(data)
    })